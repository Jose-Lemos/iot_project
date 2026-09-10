import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Conectado con código {rc}")
    client.subscribe("sensores/datos")

def on_message(client, userdata, msg):
    print(f"DEBUG MQTT: Recibí en {msg.topic} -> {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Usa el nombre del servicio 'mosquitto' igual que en tu docker-compose
client.connect("mosquitto", 1883, 60)
client.loop_forever()