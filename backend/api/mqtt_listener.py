import json
import os
import paho.mqtt.client as mqtt
import django

# Inicializar Django para poder usar los Modelos fuera del servidor web
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_project.settings')
django.setup()

from api.models import Medicion, Dispositivo, Alerta

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = 1883
MQTT_TOPIC = "sensores/datos"

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"📡 Conectado al broker MQTT. Suscribiéndose a: {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # El ESP8266 debe mandar un JSON como: 
        # {"dispositivo_id": 1, "temperatura": 24.5, "humedad": 60.0, "gas": 120.0, "riesgo": "Bajo"}
        payload = json.loads(msg.payload.decode())
        print(f"📥 Datos recibidos: {payload}")

        # Buscar o crear el dispositivo por ID
        dispositivo, _ = Dispositivo.objects.get_or_create(
            id=payload["dispositivo_id"],
            defaults={"nombre": f"Sensor ESP8266-{payload['dispositivo_id']}", "ubicacion": "Feria de Ciencias"}
        )

        # Guardar la medición
        Medicion.objects.create(
            temperatura=payload["temperatura"],
            humedad=payload["humedad"],
            gas=payload["gas"],
            riesgo=payload["riesgo"],
            sensor=dispositivo
        )

        # Lógica de Alerta Automática (Ejemplo: Gas muy alto)
        if payload["gas"] > 300: # Ajusta el umbral según tu sensor
            Alerta.objects.create(
                tipo="Fuga de Gas Detectada",
                descripcion=f"El sensor {dispositivo.nombre} reportó niveles críticos de gas: {payload['gas']} ppm.",
                atendida=False
            )

    except Exception as e:
        print(f"❌ Error al procesar mensaje MQTT: {e}")

if __name__ == "__main__":
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()