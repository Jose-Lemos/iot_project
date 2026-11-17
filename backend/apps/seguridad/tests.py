from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import PerfilSeguridad


class SeguridadApiTests(APITestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='demo',
            password='user',
        )

    @override_settings(DEBUG=True)
    def test_demo_user_is_created_with_forced_password_change(self):
        salida = StringIO()

        call_command('create_demo_user', stdout=salida)

        usuario = get_user_model().objects.get(username='user')
        self.assertTrue(usuario.check_password('user'))
        self.assertTrue(usuario.perfil_seguridad.debe_cambiar_contrasena)

    @override_settings(DEBUG=False)
    def test_demo_user_command_is_disabled_outside_debug(self):
        with self.assertRaises(CommandError):
            call_command('create_demo_user', stdout=StringIO())

    def test_api_requires_authentication(self):
        response = self.client.get('/api/mediciones/')

        self.assertEqual(response.status_code, 401)

    def test_expired_api_token_is_rejected_and_deleted(self):
        token = Token.objects.create(user=self.usuario)
        Token.objects.filter(pk=token.pk).update(
            created=timezone.now() - timedelta(hours=13)
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get('/api/mediciones/')

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())

    def test_login_returns_token_and_password_change_requirement(self):
        PerfilSeguridad.objects.create(
            usuario=self.usuario,
            debe_cambiar_contrasena=True,
        )

        response = self.client.post(
            '/seguridad/ingreso/',
            {'username': 'demo', 'password': 'user'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['must_change_password'])
        self.assertTrue(Token.objects.filter(user=self.usuario).exists())

    def test_forced_password_change_blocks_api_until_password_is_updated(self):
        PerfilSeguridad.objects.create(
            usuario=self.usuario,
            debe_cambiar_contrasena=True,
        )
        token = Token.objects.create(user=self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        blocked_response = self.client.get('/api/mediciones/')
        change_response = self.client.post(
            '/seguridad/cambiar-contrasena/',
            {
                'contrasena_actual': 'user',
                'nueva_contrasena': 'N3w!Secure-Passphrase-2026',
                'confirmar_contrasena': 'N3w!Secure-Passphrase-2026',
            },
            format='json',
        )

        self.assertEqual(blocked_response.status_code, 403)
        self.assertEqual(change_response.status_code, 200)
        self.assertFalse(change_response.data['must_change_password'])
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('N3w!Secure-Passphrase-2026'))

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {change_response.data['token']}"
        )
        self.assertEqual(self.client.get('/api/mediciones/').status_code, 200)
