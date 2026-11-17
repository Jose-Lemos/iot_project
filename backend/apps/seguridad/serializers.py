from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class IngresoSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )


class CambioContrasenaSerializer(serializers.Serializer):
    contrasena_actual = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )
    nueva_contrasena = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )
    confirmar_contrasena = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, datos):
        usuario = self.context['request'].user
        if not usuario.check_password(datos['contrasena_actual']):
            raise serializers.ValidationError({
                'contrasena_actual': 'La contraseña actual no es correcta.'
            })
        if datos['nueva_contrasena'] != datos['confirmar_contrasena']:
            raise serializers.ValidationError({
                'confirmar_contrasena': 'Las contraseñas nuevas no coinciden.'
            })
        try:
            validate_password(datos['nueva_contrasena'], user=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                'nueva_contrasena': list(error.messages)
            }) from error
        return datos
