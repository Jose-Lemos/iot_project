from django.test import TestCase
from rest_framework.test import APITestCase
from unittest.mock import patch
from types import SimpleNamespace

from .models import Alerta, Dispositivo, Medicion, UmbralConfig
from .mqtt_listener import on_connect, on_message


class MeasurementStatisticsTests(APITestCase):
	def test_statistics_include_co_in_chart_data(self):
		dispositivo = Dispositivo.objects.create(
			nombre="Sensor de prueba",
			ubicacion="Laboratorio",
		)
		Medicion.objects.create(
			sensor=dispositivo,
			temperatura=24.5,
			humedad=48,
			gas=12,
			co=3,
			riesgo="Bajo",
		)

		response = self.client.get("/api/alertas/estadisticas/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["grafico"]["co"], [3])


class MQTTListenerTests(TestCase):
	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_sends_startup_telegram_once_after_mqtt_connect(
		self, enviar_alerta_telegram
	):
		client = SimpleNamespace(subscribe=lambda *args: None)

		on_connect(client, None, None, 0)
		on_connect(client, None, None, 0)

		enviar_alerta_telegram.assert_called_once_with(
			"El sistema ambiental está en funcionamiento y comenzó el monitoreo.",
			titulo="🌿 SISTEMA AMBIENTAL 🌿",
		)

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_does_not_send_startup_telegram_when_mqtt_connection_fails(
		self, enviar_alerta_telegram
	):
		client = SimpleNamespace(subscribe=lambda *args: None)

		on_connect(client, None, None, 1)

		enviar_alerta_telegram.assert_not_called()

	def test_saves_measurement_from_data_topic(self):
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"id": 17, "temperatura": 24.5, "humedad": 48, "gas": 12, "CO": 3}',
		)

		on_message(client, None, message)

		medicion = Medicion.objects.get()
		self.assertEqual(medicion.sensor_id, 17)
		self.assertEqual(medicion.temperatura, 24.5)
		self.assertEqual(medicion.humedad, 48)
		self.assertEqual(medicion.gas, 12)
		self.assertEqual(medicion.co, 3)

	def test_ignores_non_measurement_topics(self):
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(topic="sensores/estado", payload=b'{"estado":"activo"}')

		on_message(client, None, message)

		self.assertEqual(Medicion.objects.count(), 0)
		self.assertEqual(Dispositivo.objects.count(), 0)

	def test_rejects_measurements_with_invalid_values(self):
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"temperatura": 24.5, "humedad": 140, "gas": 12}',
		)

		on_message(client, None, message)

		self.assertEqual(Medicion.objects.count(), 0)

	def test_saves_measurement_from_esp_scalar_topics(self):
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		readings = [
			("control/temperatura", b"24.5"),
			("control/humedad", b"48.0"),
			("control/co", b"3.0"),
			("control/gas", b"12.0"),
		]

		for topic, payload in readings:
			on_message(client, None, SimpleNamespace(topic=topic, payload=payload))

		medicion = Medicion.objects.get()
		self.assertEqual(medicion.sensor_id, 1)
		self.assertEqual(medicion.temperatura, 24.5)
		self.assertEqual(medicion.humedad, 48.0)
		self.assertEqual(medicion.co, 3.0)
		self.assertEqual(medicion.gas, 12.0)

	def test_does_not_reuse_previous_cycle_when_dht_readings_are_missing(self):
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		for topic, payload in [
			("control/temperatura", b"24.5"),
			("control/humedad", b"48.0"),
			("control/co", b"3.0"),
			("control/gas", b"12.0"),
			("control/co", b"3.1"),
			("control/gas", b"12.1"),
		]:
			on_message(client, None, SimpleNamespace(topic=topic, payload=payload))

		self.assertEqual(Medicion.objects.count(), 1)

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_sends_telegram_when_configured_threshold_is_exceeded(
		self, enviar_alerta_telegram
	):
		UmbralConfig.objects.create(gas_max=100)
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"temperatura": 24.5, "humedad": 48, "gas": 120, "CO": 3}',
		)

		on_message(client, None, message)

		enviar_alerta_telegram.assert_called_once()
		self.assertEqual(Alerta.objects.get().tipo, "Peligro")

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_saves_and_sends_telegram_for_high_carbon_monoxide(
		self, enviar_alerta_telegram
	):
		UmbralConfig.objects.create(gas_max=100)
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"temperatura": 24.5, "humedad": 48, "gas": 12, "CO": 120}',
		)

		on_message(client, None, message)

		alerta = Alerta.objects.get()
		self.assertEqual(alerta.tipo, "Peligro - Monóxido")
		self.assertIn("Monóxido de carbono: 120.0 ppm", alerta.descripcion)
		enviar_alerta_telegram.assert_called_once_with(alerta.descripcion)

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_saves_separate_alerts_when_gas_and_carbon_monoxide_are_high(
		self, enviar_alerta_telegram
	):
		UmbralConfig.objects.create(gas_max=100)
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"temperatura": 24.5, "humedad": 48, "gas": 120, "CO": 130}',
		)

		on_message(client, None, message)

		alertas = list(Alerta.objects.order_by("tipo"))
		self.assertEqual(len(alertas), 2)
		self.assertEqual(
			{alerta.tipo for alerta in alertas},
			{"Peligro", "Peligro - Monóxido"},
		)
		self.assertTrue(any("Gas: 120.0 ppm" in alerta.descripcion for alerta in alertas))
		self.assertTrue(
			any("Monóxido de carbono: 130.0 ppm" in alerta.descripcion for alerta in alertas)
		)
		self.assertEqual(enviar_alerta_telegram.call_count, 2)

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_gas_alert_does_not_suppress_carbon_monoxide_alert(
		self, enviar_alerta_telegram
	):
		UmbralConfig.objects.create(gas_max=100)
		Alerta.objects.create(
			tipo="Peligro", descripcion="Alerta de gas activa", atendida=False
		)
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"temperatura": 24.5, "humedad": 48, "gas": 12, "CO": 120}',
		)

		on_message(client, None, message)

		alerta_co = Alerta.objects.get(tipo="Peligro - Monóxido")
		self.assertIn("Monóxido de carbono: 120.0 ppm", alerta_co.descripcion)
		enviar_alerta_telegram.assert_called_once_with(alerta_co.descripcion)

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_sends_telegram_for_carbon_monoxide_risk_alert(
		self, enviar_alerta_telegram
	):
		UmbralConfig.objects.create(gas_max=100)
		client = SimpleNamespace(publish=lambda *args, **kwargs: None)
		message = SimpleNamespace(
			topic="sensores/datos",
			payload=b'{"temperatura": 24.5, "humedad": 48, "gas": 12, "CO": 60}',
		)

		on_message(client, None, message)

		alerta = Alerta.objects.get()
		self.assertEqual(alerta.tipo, "Riesgo - Monóxido")
		enviar_alerta_telegram.assert_called_once_with(alerta.descripcion)

	@patch("api.mqtt_listener.enviar_alerta_telegram")
	def test_sends_telegram_when_device_reports_danger_once_per_transition(
		self, enviar_alerta_telegram
	):
		client = SimpleNamespace(
			publish=lambda *args, **kwargs: None,
			_latest_readings={
				"temperatura": 46.0,
				"humedad": 42.0,
				"co": 15.0,
				"gas": 120.0,
			},
		)
		message = SimpleNamespace(topic="control/estado", payload=b"rojo")

		on_message(client, None, message)
		on_message(client, None, message)

		enviar_alerta_telegram.assert_called_once()
		alerta = Alerta.objects.get()
		self.assertEqual(alerta.tipo, "Peligro")
		self.assertIn("Temperatura: 46.0 °C", alerta.descripcion)
		self.assertIn("Gas: 120.0 ppm", alerta.descripcion)
