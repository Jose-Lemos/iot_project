from django.db import models

class Dispositivo(models.Model):
    nombre = models.CharField(db_index=True, max_length=100)
    ubicacion = models.CharField(max_length=150)
    estado = models.BooleanField(default=True) # True = Activo, False = Inactivo

    def __str__(self):
        return self.nombre

class Medicion(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    temperatura = models.FloatField()
    humedad = models.FloatField()
    gas = models.FloatField()
    riesgo = models.CharField(max_length=50) # Ejemplo: "Bajo", "Alto"
    sensor = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='mediciones')

class Alerta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=100) # Ejemplo: "Fuga de Gas", "Alta Temperatura"
    descripcion = models.TextField()
    atendida = models.BooleanField(default=False)

class UmbralConfig(models.Model):
    temp_max = models.FloatField(default=35.0)
    gas_max = models.FloatField(default=300.0)
    humedad_min = models.FloatField(default=20.0)

    def save(self, *args, **kwargs):
        # Aseguramos que solo exista una fila de configuración
        self.pk = 1
        super(UmbralConfig, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass # Evitar que borren la configuración por error