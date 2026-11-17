from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView

from .models import PerfilSeguridad
from .serializers import CambioContrasenaSerializer, IngresoSerializer


class IngresoView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, ScopedRateThrottle]
    throttle_scope = 'auth_login'

    def post(self, request):
        serializer = IngresoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if usuario is None or not usuario.is_active:
            return Response(
                {'error': 'El usuario o la contraseña no son correctos.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        Token.objects.filter(user=usuario).delete()
        token = Token.objects.create(user=usuario)
        perfil, _ = PerfilSeguridad.objects.get_or_create(usuario=usuario)
        return Response({
            'token': token.key,
            'must_change_password': perfil.debe_cambiar_contrasena,
        })


class SesionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil, _ = PerfilSeguridad.objects.get_or_create(usuario=request.user)
        return Response({
            'username': request.user.get_username(),
            'must_change_password': perfil.debe_cambiar_contrasena,
        })


class CambioContrasenaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambioContrasenaSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        usuario = request.user
        usuario.set_password(serializer.validated_data['nueva_contrasena'])
        usuario.save(update_fields=['password'])
        perfil, _ = PerfilSeguridad.objects.get_or_create(usuario=usuario)
        perfil.debe_cambiar_contrasena = False
        perfil.save(update_fields=['debe_cambiar_contrasena'])

        Token.objects.filter(user=usuario).delete()
        token = Token.objects.create(user=usuario)
        return Response({
            'token': token.key,
            'must_change_password': False,
        })


class SalidaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
