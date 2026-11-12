import json
import math
import os
import traceback
import re
import django
import paho.mqtt.client as mqtt
from django.db import transaction
import requests

# Inicializar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_project.settings')
django.setup()

from api.models import Medicion, Dispositivo, Alerta, UmbralConfig

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_TIMEOUT = 10

TOPICS = [
    ("sensores/datos", 0),
    ("sensores/estado", 0),
    ("sensores/config", 0),
    ("control/temperatura", 0),
    ("control/humedad", 0),
    ("control/co", 0),
    ("control/gas", 0),
    ("control/estado", 0),
]

SENSOR_TOPICS = {
    "control/temperatura": "temperatura",
    "control/humedad": "humedad",
    "control/co": "co",
    "control/gas": "gas",
}


def enviar_alerta_telegram(mensaje, titulo="🚨 ALERTA DE SISTEMA EMBEBIDO 🚨"):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ℹ️ Telegram no configurado; se omite la notificación.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"{titulo}\n\n{mensaje}",
    }
    try:
        response = requests.post(url, json=payload, timeout=TELEGRAM_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"❌ Error al enviar alerta por Telegram: {error}")


def _parse_payload(raw_payload):
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        # Some firmware versions send JSON object keys without quotes.
        json_limpio = re.sub(
            r'([{,]\s*)([A-Za-z_]\w*)(\s*:)', r'\1"\2"\3', raw_payload
        )
        payload = json.loads(json_limpio)
    if not isinstance(payload, dict):
        raise ValueError("El mensaje MQTT debe ser un objeto JSON")
    return payload


def _number(payload, *keys, default=None):
    value = next((payload[key] for key in keys if key in payload), default)
    if value is None or isinstance(value, bool):
        raise ValueError(f"Falta un valor numérico válido para {keys[0]}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"El valor de {keys[0]} debe ser finito")
    return value


def _registrar_alerta_contaminante(client, nombre, valor, umbral, tipo_peligro):
    if valor <= 50:
        return False

    es_peligro = valor > umbral
    tipo = tipo_peligro if es_peligro else (
        "Riesgo" if nombre == "Gas" else "Riesgo - Monóxido"
    )
    if Alerta.objects.filter(tipo=tipo, atendida=False).exists():
        return False

    descripcion = f"Nivel {'crítico' if es_peligro else 'elevado'} - {nombre}: {valor} ppm"
    Alerta.objects.create(tipo=tipo, descripcion=descripcion, atendida=False)

    if es_peligro or nombre == "Monóxido de carbono":
        enviar_alerta_telegram(descripcion)

    if es_peligro:
        client.publish(
            "control/alarma_led",
            json.dumps({
                "estado": "PELIGRO",
                "led": {"color": "red", "parpadeo": True, "intervalo": 500},
                "buzzer": {"activo": True, "duracion": 10000},
                "display": {"mensaje": "PELIGRO\nVentilar"}
            })
        )
        return True
    return False


def _save_measurement(client, payload):
    dispositivo_id = payload.get("dispositivo_id", payload.get("id", 1))
    if isinstance(dispositivo_id, bool):
        raise ValueError("El identificador del dispositivo no es válido")
    dispositivo_id = int(dispositivo_id)
    if dispositivo_id < 1:
        raise ValueError("El identificador del dispositivo debe ser positivo")

    temperatura = _number(payload, "temperatura", "temperature")
    humedad = _number(payload, "humedad", "humidity")
    gas = _number(payload, "gas", "mq2", default=0.0)
    co_nivel = _number(payload, "CO", "co", "mq7", default=0.0)
    if gas < 0 or co_nivel < 0:
        raise ValueError("Las lecturas de gas y CO no pueden ser negativas")
    if not 0 <= humedad <= 100:
        raise ValueError("La humedad debe estar entre 0 y 100")

    client._latest_readings = {
        "temperatura": temperatura,
        "humedad": humedad,
        "gas": gas,
        "co": co_nivel,
    }

    with transaction.atomic():
        dispositivo, _ = Dispositivo.objects.get_or_create(
            id=dispositivo_id,
            defaults={
                "nombre": f"Sensor Vital Air-{dispositivo_id}",
                "ubicacion": "Feria de Ciencias"
            }
        )

        config, _ = UmbralConfig.objects.get_or_create(pk=1)
        max_contaminante = max(gas, co_nivel)
        peligro_nuevo = False

        peligro_nuevo |= _registrar_alerta_contaminante(
            client, "Gas", gas, config.gas_max, "Peligro"
        )
        peligro_nuevo |= _registrar_alerta_contaminante(
            client, "Monóxido de carbono", co_nivel, config.gas_max,
            "Peligro - Monóxido"
        )

        if max_contaminante <= 25:
            riesgo = "Seguro"
        elif max_contaminante <= 50:
            riesgo = "Precaución"
        elif max_contaminante <= config.gas_max:
            riesgo = "Riesgo"
        else:
            riesgo = "Peligro"

        medicion = Medicion.objects.create(
            temperatura=temperatura,
            humedad=humedad,
            gas=gas,
            co=co_nivel,
            riesgo=riesgo,
            sensor=dispositivo
        )
    if peligro_nuevo:
        print("🚨 Alerta crítica de contaminante enviada.")
    print(f"✅ Medición guardada exitosamente [ID: {medicion.id}] - Riesgo: {riesgo}")


def _handle_device_state(client, payload):
    estado = payload.decode("utf-8").strip().lower()
    if estado not in {"verde", "amarillo", "rojo", "calentando"}:
        print(f"⚠️ Estado de dispositivo desconocido: {estado!r}")
        return

    estado_anterior = getattr(client, "_device_state", None)
    client._device_state = estado
    if estado != "rojo" or estado_anterior == "rojo":
        return

    if Alerta.objects.filter(
        tipo__in=("Peligro", "Peligro - Monóxido"), atendida=False
    ).exists():
        return

    lecturas = getattr(client, "_latest_readings", {})
    detalle = "\n".join(
        f"{nombre}: {lecturas[campo]:.1f} {unidad}"
        for campo, nombre, unidad in (
            ("temperatura", "Temperatura", "°C"),
            ("humedad", "Humedad", "%"),
            ("co", "Monóxido de carbono", "ppm"),
            ("gas", "Gas", "ppm"),
        )
        if campo in lecturas
    )
    descripcion = "El sensor detectó un ambiente peligroso (estado rojo)."
    if detalle:
        descripcion = f"{descripcion}\n{detalle}"

    Alerta.objects.create(
        tipo="Peligro",
        descripcion=descripcion,
        atendida=False,
    )
    enviar_alerta_telegram(descripcion)


# --- Callbacks compatibles con Paho MQTT VERSION2 ---

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"📡 Conectado exitosamente al broker MQTT. Suscribiéndose a: {TOPICS}")
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
        if not getattr(client, "_startup_notified", False):
            client._startup_notified = True
            enviar_alerta_telegram(
                "El sistema ambiental está en funcionamiento y comenzó el monitoreo.",
                titulo="🌿 SISTEMA AMBIENTAL 🌿",
            )
    else:
        print(f"❌ Error al conectar con el broker. Código: {reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    print(f"⚠️ Desconectado del broker MQTT (Código: {reason_code}). Intentando reconectar...")

def on_message(client, userdata, msg):
    if msg.topic == "control/estado":
        try:
            _handle_device_state(client, msg.payload)
        except Exception as e:
            print(f"❌ Error al procesar estado del dispositivo: {e}")
            traceback.print_exc()
        return

    if msg.topic in SENSOR_TOPICS:
        try:
            readings = getattr(client, "_sensor_readings", {})
            field = SENSOR_TOPICS[msg.topic]
            value = float(msg.payload.decode("utf-8"))
            if not math.isfinite(value):
                raise ValueError(f"El valor de {field} debe ser finito")
            readings[field] = value

            if field == "gas":
                client._sensor_readings = {}
                if not all(key in readings for key in ("temperatura", "humedad", "co", "gas")):
                    print("ℹ️ Ciclo de sensores incompleto; no se guarda la medición.")
                    return
                _save_measurement(client, readings)
            else:
                client._sensor_readings = readings
        except Exception as e:
            if msg.topic == "control/gas":
                client._sensor_readings = {}
            print(f"❌ Error al procesar lectura MQTT de {msg.topic}: {e}")
            traceback.print_exc()
        return

    if msg.topic != "sensores/datos":
        print(f"ℹ️ Mensaje ignorado en tópico no destinado a mediciones: {msg.topic}")
        return

    try:
        mensaje_crudo = msg.payload.decode('utf-8')
        print(f"DEBUG: Tópico {msg.topic}, Mensaje crudo: '{mensaje_crudo}'")
        payload = _parse_payload(mensaje_crudo)
        print(f"📥 Datos decodificados: {payload}")
        _save_measurement(client, payload)

    except Exception as e:
        print(f"❌ Error al procesar mensaje MQTT: {e}")
        traceback.print_exc()

# --- Punto de entrada del Script ---
if __name__ == "__main__":
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="iot_worker_listener"
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"Connecting to MQTT Broker in {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()