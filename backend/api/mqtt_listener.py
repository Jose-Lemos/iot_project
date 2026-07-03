import json
import os
import sys
import paho.mqtt.client as mqtt
import django

# Agregamos el directorio actual y el padre al path de Python
sys.path.append('/app')
sys.path.append('/app/iot_project')

# Inicializar Django para poder usar los Modelos fuera del servidor web
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_project.settings')
django.setup()


from api.models import Medicion, Dispositivo, Alerta

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = 1883
#MQTT_TOPIC = "sensores/datos"
TOPICS=[

("sensores/datos",0),

("sensores/estado",0),

("sensores/config",0)

]

def on_disconnect(client, userdata, flags, rc, properties=None):
    print(f"📡 Desconectado del broker MQTT")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"📡 Conectado al broker MQTT. Suscribiéndose a los temas: {TOPICS}")
    for topic, qos in TOPICS:
        client.subscribe(topic, qos)

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

        gas = payload["gas"]

        if gas <= 25:
            riesgo = "Seguro"

        elif gas <= 50:
            riesgo = "Precaución"

        elif gas <= 100:
            riesgo = "Riesgo"
            Alerta.objects.create(
                tipo="Riesgo",
                descripcion=f"Nivel elevado: {payload['gas']} ppm",
                atendida=False
            )

        else:  #solo cuando el estado es de peligro, mandamos una alerta de tipo Peligro y además enviamos el mensaje por MQTT para activar el led y la alarma
            riesgo = "Peligro"
            Alerta.objects.create(
                tipo="Peligro",
                descripcion=f"Nivel crítico: {payload['gas']} ppm",
                atendida=False
            )
            client.publish(
                "control/alarma_led",
                json.dumps({
                    "estado": "PELIGRO",
                    "led": {
                        "color": "red",
                        "parpadeo": True,
                        "intervalo": 500
                    },
                    "buzzer": {
                        "activo": True,
                        "duracion": 10000
                    },
                    "display": {
                        "mensaje": "PELIGRO\nVentilar"
                    }
                })
            )

        # Guardar la medición
        Medicion.objects.create(
            temperatura=payload["temperatura"],
            humedad=payload["humedad"],
            gas=payload["gas"],
            riesgo=riesgo,
            sensor=dispositivo
        )

            

    except Exception as e:
        print(f"❌ Error al procesar mensaje MQTT: {e}")

if __name__ == "__main__":
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.reconnect_delay_set(
        min_delay=1,
        max_delay=30
    )

    #client.connect(MQTT_BROKER, MQTT_PORT, 60)
    #client.loop_forever()