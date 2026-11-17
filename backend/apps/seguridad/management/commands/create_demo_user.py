from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.seguridad.models import PerfilSeguridad


class Command(BaseCommand):
    help = 'Crea user/user para una demo local; exige cambiar la contraseña al ingresar.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'La cuenta user/user solo se puede crear con DJANGO_DEBUG=true.'
            )

        usuario, creado = get_user_model().objects.get_or_create(
            username='user',
            defaults={'is_active': True},
        )
        if creado:
            usuario.set_password('user')
            usuario.save(update_fields=['password'])

        perfil, perfil_creado = PerfilSeguridad.objects.get_or_create(
            usuario=usuario,
            defaults={'debe_cambiar_contrasena': creado},
        )
        if (
            not creado
            and perfil_creado
            and usuario.check_password('user')
            and not perfil.debe_cambiar_contrasena
        ):
            perfil.debe_cambiar_contrasena = True
            perfil.save(update_fields=['debe_cambiar_contrasena'])
        if creado:
            self.stdout.write(self.style.SUCCESS(
                'Se creó user/user. La cuenta exigirá cambiar la contraseña al ingresar.'
            ))
        else:
            self.stdout.write('El usuario user ya existe; no se modificó su contraseña.')
