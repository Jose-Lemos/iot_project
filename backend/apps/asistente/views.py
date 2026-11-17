from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import (
    ProviderError,
    ProviderUnavailableError,
    generar_respuesta,
    obtener_contexto_mediciones,
)


MAX_MENSAJE_CARACTERES = 1000
MAX_MENSAJES_HISTORIAL = 10


class ChatView(APIView):
    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {'error': 'El cuerpo de la solicitud debe ser un objeto JSON.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        mensaje = request.data.get('message')
        historial = request.data.get('history', [])

        if not isinstance(mensaje, str) or not mensaje.strip():
            return Response(
                {'error': 'Escribí una pregunta para el asistente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(mensaje) > MAX_MENSAJE_CARACTERES:
            return Response(
                {'error': 'La pregunta no puede superar los 1000 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(historial, list) or len(historial) > MAX_MENSAJES_HISTORIAL:
            return Response(
                {'error': 'El historial enviado no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if any(
            not isinstance(item, dict)
            or item.get('role') not in ('user', 'assistant')
            or not isinstance(item.get('content'), str)
            or not item['content'].strip()
            or len(item['content']) > MAX_MENSAJE_CARACTERES
            for item in historial
        ):
            return Response(
                {'error': 'El historial enviado no es válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contexto = obtener_contexto_mediciones()
        try:
            respuesta = generar_respuesta(mensaje.strip(), historial, contexto)
        except ProviderUnavailableError as error:
            return Response(
                {'error': str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ProviderError as error:
            return Response(
                {'error': str(error)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'reply': respuesta})
