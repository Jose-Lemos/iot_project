from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AutenticacionTokenConVencimiento(TokenAuthentication):
    def authenticate_credentials(self, key):
        usuario, token = super().authenticate_credentials(key)
        if token.created < timezone.now() - timedelta(hours=12):
            token.delete()
            raise AuthenticationFailed('La sesión venció. Volvé a ingresar.')
        return usuario, token
