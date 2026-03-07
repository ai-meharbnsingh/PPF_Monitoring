import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = "192.168.29.115"
MQTT_PORT = 1883
TOPIC = "workshop/+/pit/+/sensors"

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to Pi MQTT ({MQTT_BROKER})")
    print(f"📡 Subscribing to: {TOPIC}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"\n📥 [{msg.topic}] Sensor Data from {data.get('device_id', 'Unknown')}:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error parsing message: {e}")
        print(f"Raw: {msg.payload.decode()}")

client = mqtt.Client(client_id="debug-listener")
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
