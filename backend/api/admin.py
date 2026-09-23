from django.contrib import admin
from .models import Dispositivo, Medicion, Alerta, UmbralConfig

# (Opcional) Personalización visual para que las tablas se vean más ordenadas en el Admin
@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'ubicacion', 'estado')
    search_fields = ('nombre', 'ubicacion')

@admin.register(Medicion)
class MedicionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sensor', 'temperatura', 'humedad', 'gas', 'riesgo', 'fecha')
    list_filter = ('riesgo', 'sensor', 'fecha')
    search_fields = ('sensor__nombre',)

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'descripcion', 'atendida', 'fecha')
    list_filter = ('tipo', 'atendida', 'fecha')
    search_fields = ('descripcion',)

@admin.register(UmbralConfig)
class UmbralConfigAdmin(admin.ModelAdmin):
    list_display = ('temp_max', 'gas_max', 'humedad_min')