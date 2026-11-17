from django.conf import settings
from django.db import models


class PerfilSeguridad(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_seguridad',
    )
    debe_cambiar_contrasena = models.BooleanField(default=False)
