import paho.mqtt.client as mqtt

TOPIC = "senai510/mhss/mov"
PAYLOAD_BRUTO_TESTE = '{"movimento":"centro","x":1826,"y":1827}'


def publicar_teste(client):
    resultado = client.publish(TOPIC, PAYLOAD_BRUTO_TESTE, qos=1)
    if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Teste publicado em {TOPIC}: {PAYLOAD_BRUTO_TESTE}")
    else:
        print(f"Falha ao publicar o teste. Código MQTT: {resultado.rc}")


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Conectado, código: {reason_code}")
    client.subscribe(TOPIC)
    publicar_teste(client)


def on_message(client, userdata, msg):
    print(f"TÓPICO: {msg.topic} | PAYLOAD: {repr(msg.payload)}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 60)
# client.loop_forever()
