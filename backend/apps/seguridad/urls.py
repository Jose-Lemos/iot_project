from django.urls import path

from .views import CambioContrasenaView, IngresoView, SalidaView, SesionView

urlpatterns = [
    path('ingreso/', IngresoView.as_view(), name='seguridad-ingreso'),
    path('sesion/', SesionView.as_view(), name='seguridad-sesion'),
    path('cambiar-contrasena/', CambioContrasenaView.as_view(), name='seguridad-cambiar-contrasena'),
    path('salida/', SalidaView.as_view(), name='seguridad-salida'),
]
