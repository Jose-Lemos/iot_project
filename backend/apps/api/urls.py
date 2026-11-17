from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DispositivoViewSet, MedicionViewSet, AlertaViewSet, UmbralConfigDetailView

router = DefaultRouter()
router.register(r'dispositivos', DispositivoViewSet)
router.register(r'mediciones', MedicionViewSet)
router.register(r'alertas', AlertaViewSet)

urlpatterns = [
    # Tus endpoints automáticos
    *router.urls,
    
    # Tu nuevo endpoint para la configuración
    path('configuracion/', UmbralConfigDetailView.as_view(), name='configuracion-umbrales'),
]