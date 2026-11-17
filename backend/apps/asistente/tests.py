import json
import os
from datetime import timedelta
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.api.models import Alerta, Dispositivo, Medicion, UmbralConfig
from .services import (
    MAX_MEDICIONES,
    ProviderError,
    ejecutar_herramienta,
    obtener_contexto_mediciones,
)


ZONA_ARGENTINA = ZoneInfo('America/Argentina/Buenos_Aires')


class ContextoMedicionesTests(TestCase):
    def setUp(self):
        self.sensor = Dispositivo.objects.create(
            nombre='Sensor de prueba',
            ubicacion='Laboratorio',
        )

    def crear_medicion(self, temperatura):
        return Medicion.objects.create(
            sensor=self.sensor,
            temperatura=temperatura,
            humedad=45,
            gas=12,
            co=3,
            riesgo='Bajo',
        )

    def test_reads_only_the_latest_sixty_measurements(self):
        for temperatura in range(MAX_MEDICIONES + 5):
            self.crear_medicion(temperatura)

        contexto = obtener_contexto_mediciones()

        self.assertEqual(len(contexto['mediciones']), MAX_MEDICIONES)
        self.assertEqual(contexto['mediciones'][0]['temperatura_c'], 5)
        self.assertEqual(contexto['mediciones'][-1]['temperatura_c'], 64)

    def test_includes_current_configured_thresholds(self):
        UmbralConfig.objects.create(temp_max=32, gas_max=80, humedad_min=25)
        self.crear_medicion(24)

        contexto = obtener_contexto_mediciones()

        self.assertEqual(
            contexto['umbrales_configurados'],
            {
                'temperatura_maxima_c': 32,
                'gas_maximo_ppm': 80,
                'humedad_minima_pct': 25,
                'co_ppm': 'No hay un umbral de CO configurado.',
            },
        )

    def test_historical_measurement_query_filters_dates_and_caps_rows(self):
        ahora = timezone.now()
        self.crear_medicion(20)
        Medicion.objects.filter().update(fecha=ahora - timedelta(days=2))
        for temperatura in (22, 23):
            self.crear_medicion(temperatura)
        argumentos = json.dumps({
            'desde': (ahora - timedelta(minutes=5)).astimezone(ZONA_ARGENTINA).isoformat(),
            'hasta': (ahora + timedelta(minutes=5)).astimezone(ZONA_ARGENTINA).isoformat(),
            'limite': 100,
        })

        resultado = ejecutar_herramienta('consultar_mediciones', argumentos)

        self.assertEqual(resultado['limite_aplicado'], 60)
        self.assertEqual(
            [fila['temperatura_c'] for fila in resultado['resultados']],
            [22, 23],
        )

    def test_historical_alert_query_filters_status_and_time_range(self):
        ahora = timezone.now()
        alerta = Alerta.objects.create(
            tipo='Peligro',
            descripcion='Nivel elevado',
            atendida=False,
        )
        argumentos = json.dumps({
            'desde': (ahora - timedelta(minutes=5)).astimezone(ZONA_ARGENTINA).isoformat(),
            'hasta': (ahora + timedelta(minutes=5)).astimezone(ZONA_ARGENTINA).isoformat(),
            'atendida': False,
        })

        resultado = ejecutar_herramienta('consultar_alertas', argumentos)

        self.assertEqual(len(resultado['resultados']), 1)
        self.assertEqual(resultado['resultados'][0]['tipo'], alerta.tipo)
        self.assertFalse(resultado['resultados'][0]['atendida'])

    def test_historical_query_rejects_invalid_tool_arguments(self):
        with self.assertRaises(ProviderError):
            ejecutar_herramienta(
                'consultar_mediciones',
                json.dumps({'desde': 'ayer', 'hasta': 'mañana'}),
            )


class ChatViewTests(APITestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='test-user',
            password='test-password',
        )
        self.client.force_authenticate(usuario)

    @patch.dict(os.environ, {}, clear=True)
    def test_reports_missing_provider_configuration(self):
        response = self.client.post(
            '/asistente/chat/',
            {'message': '¿Qué recomendás?'},
            format='json',
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn('GROQ_API_KEY', response.data['error'])

    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'})
    @patch('apps.asistente.services.requests.post')
    def test_sends_live_measurement_context_to_provider(self, post):
        sensor = Dispositivo.objects.create(
            nombre='Sensor de prueba',
            ubicacion='Laboratorio',
        )
        Medicion.objects.create(
            sensor=sensor,
            temperatura=24.5,
            humedad=45,
            gas=12,
            co=3,
            riesgo='Bajo',
        )
        provider_response = Mock()
        provider_response.json.return_value = {
            'choices': [{'message': {'content': 'Ventilá el ambiente.'}}]
        }
        post.return_value = provider_response

        response = self.client.post(
            '/asistente/chat/',
            {'message': '¿Qué recomendás?'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['reply'], 'Ventilá el ambiente.')
        provider_context = post.call_args.kwargs['json']['messages'][0]['content']
        self.assertIn('"temperatura_c": 24.5', provider_context)
        self.assertIn('"sensor": "Sensor de prueba"', provider_context)

    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'})
    @patch('apps.asistente.services.requests.post')
    def test_ai_can_request_a_historical_alert_query(self, post):
        ahora = timezone.now()
        alerta = Alerta.objects.create(
            tipo='Peligro',
            descripcion='Gas por encima del umbral',
            atendida=False,
        )
        arguments = json.dumps({
            'desde': (ahora - timedelta(minutes=5)).astimezone(ZONA_ARGENTINA).isoformat(),
            'hasta': (ahora + timedelta(minutes=5)).astimezone(ZONA_ARGENTINA).isoformat(),
        })
        tool_response = Mock()
        tool_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': None,
                    'tool_calls': [{
                        'id': 'call_alerts',
                        'type': 'function',
                        'function': {
                            'name': 'consultar_alertas',
                            'arguments': arguments,
                        },
                    }],
                },
            }],
        }
        final_response = Mock()
        final_response.json.return_value = {
            'choices': [{'message': {'content': 'Encontré una alerta de peligro.'}}],
        }
        post.side_effect = [tool_response, final_response]

        response = self.client.post(
            '/asistente/chat/',
            {'message': '¿Qué alertas hubo hace unos minutos?'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Encontré una alerta', response.data['reply'])
        follow_up_messages = post.call_args_list[1].kwargs['json']['messages']
        tool_result = next(item for item in follow_up_messages if item['role'] == 'tool')
        self.assertIn(alerta.tipo, tool_result['content'])

    def test_rejects_oversized_history(self):
        response = self.client.post(
            '/asistente/chat/',
            {
                'message': '¿Qué recomendás?',
                'history': [
                    {'role': 'user', 'content': 'pregunta'}
                    for _ in range(11)
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
