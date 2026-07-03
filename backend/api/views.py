from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Max, Count, Min
from django.utils import timezone
from datetime import timedelta
from .models import Dispositivo, Medicion, Alerta, UmbralConfig
from .serializers import DispositivoSerializer, MedicionSerializer, AlertaSerializer, UmbralConfigSerializer

class DispositivoViewSet(viewsets.ModelViewSet):
    queryset = Dispositivo.objects.all()
    serializer_class = DispositivoSerializer

class MedicionViewSet(viewsets.ModelViewSet):
    queryset = Medicion.objects.all()
    serializer_class = MedicionSerializer

class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        periodo = request.query_params.get('periodo', 'diario')
        ahora = timezone.now()

        # Configurar los rangos de tiempo hacia atrás
        if periodo == 'diario':
            fecha_inicio = ahora - timedelta(days=1)
        elif periodo == 'semanal':
            fecha_inicio = ahora - timedelta(weeks=1)
        elif periodo == 'mensual':
            fecha_inicio = ahora - timedelta(days=30)
        elif periodo == 'anual':
            fecha_inicio = ahora - timedelta(days=365)
        else:
            fecha_inicio = ahora - timedelta(days=1) # Por defecto diario

        # Filtrar mediciones por fecha
        mediciones_filtradas = Medicion.objects.filter(fecha__gte=fecha_inicio)
        alertas_filtradas = Alerta.objects.filter(fecha__gte=fecha_inicio)

        stats = mediciones_filtradas.aggregate(
            # Temperatura
            avg_temperatura=Avg('temperatura'),
            min_temperatura=Min('temperatura'),
            max_temperatura=Max('temperatura'),

            # Humedad
            avg_humedad=Avg('humedad'),
            min_humedad=Min('humedad'),
            max_humedad=Max('humedad'),

            # Gas
            avg_gas=Avg('gas'),
            max_gas=Max('gas')
        )
        total_alertas = alertas_filtradas.count()

        # Historial formateado para alimentar los gráficos de Chart.js directamente
        historial = mediciones_filtradas.order_by('fecha')
        labels = [m.fecha.strftime('%d/%m %H:%M') for m in historial]
        data_temp = [m.temperatura for m in historial]
        data_humedad = [m.humedad for m in historial]
        data_gas = [m.gas for m in historial]

        return Response({
            "periodo": periodo,
            "temperatura": {
                "promedio": round(stats["avg_temperatura"] or 0, 2),
                "minima": round(stats["min_temperatura"] or 0, 2),
                "maxima": round(stats["max_temperatura"] or 0, 2),
            },

            "humedad": {
                "promedio": round(stats["avg_humedad"] or 0, 2),
                "minima": round(stats["min_humedad"] or 0, 2),
                "maxima": round(stats["max_humedad"] or 0, 2),
            },

            "gas": {
                "promedio": round(stats["avg_gas"] or 0, 2),
                "maximo": round(stats["max_gas"] or 0, 2),
            },
            
            "total_alertas": total_alertas,
            "grafico": {
                "labels": labels,
                "temperatura": data_temp,
                "humedad": data_humedad,
                "gas": data_gas
            }
        })


class UmbralConfigDetailView(generics.RetrieveUpdateAPIView):
    queryset = UmbralConfig.objects.all()
    serializer_class = UmbralConfigSerializer

    # Forzamos a que siempre busque el registro con ID=1
    def get_object(self):
        obj, created = UmbralConfig.objects.get_or_create(pk=1)
        return obj