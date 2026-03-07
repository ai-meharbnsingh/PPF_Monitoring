import paho.mqtt.client as mqtt
import json
import time
import ssl

# HiveMQ Cloud config from .env
MQTT_BROKER = "c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "ppf_backend"
MQTT_PASSWORD = "PPF@Mqtt2026!secure"
TOPIC = "workshop/+/pit/+/sensors"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to HiveMQ Cloud ({MQTT_BROKER})")
        print(f"📡 Subscribing to: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"\n📥 [{msg.topic}] Sensor Data from {data.get('device_id', 'Unknown')}:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error parsing message: {e}")
        print(f"Raw: {msg.payload.decode()}")

client = mqtt.Client(client_id="hivemq-debug-listener")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

client.on_connect = on_connect
client.on_message = on_message

print(f"🔌 Connecting to {MQTT_BROKER}...")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    time.sleep(15) # Listen for 15 seconds
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")
