from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Max, Count
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
            avg_temperatura=Avg('temperatura'),
            max_gas=Max('gas')
        )
        total_alertas = alertas_filtradas.count()

        # Historial formateado para alimentar los gráficos de Chart.js directamente
        historial = mediciones_filtradas.order_by('fecha')
        labels = [m.fecha.strftime('%d/%m %H:%M') for m in historial]
        data_temp = [m.temperatura for m in historial]
        data_gas = [m.gas for m in historial]

        return Response({
            "periodo": periodo,
            "avg_temperatura": round(stats['avg_temperatura'] or 0, 2),
            "max_gas": round(stats['max_gas'] or 0, 2),
            "total_alertas": total_alertas,
            "grafico": {
                "labels": labels,
                "temperatura": data_temp,
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