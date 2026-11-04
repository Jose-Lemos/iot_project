from django.test import TestCase
from unittest.mock import patch
from types import SimpleNamespace

from .models import Alerta, Dispositivo, Medicion, UmbralConfig
from .mqtt_listener import on_message


class MQTTListenerTests(TestCase):
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
