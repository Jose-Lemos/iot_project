from rest_framework import serializers
from .models import Dispositivo, Medicion, Alerta, UmbralConfig

class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = '__all__'

class MedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicion
        fields = '__all__'

class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'

class UmbralConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = UmbralConfig
        fields = ['temp_max', 'gas_max', 'humedad_min']