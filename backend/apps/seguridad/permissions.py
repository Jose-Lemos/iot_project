from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission


class NoForzarCambioContrasena(BasePermission):
    message = 'Cambiá la contraseña inicial antes de usar esta función.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            perfil = request.user.perfil_seguridad
        except ObjectDoesNotExist:
            return True
        return not perfil.debe_cambiar_contrasena
