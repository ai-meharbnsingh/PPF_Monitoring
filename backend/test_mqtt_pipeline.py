"""
Test MQTT pipeline end-to-end by publishing a simulated ESP32 sensor payload.
This verifies: Mosquitto → backend MQTT service → sensor_service → DB → WebSocket
"""
import paho.mqtt.client as mqtt
import json
import time

BROKER = "localhost"
PORT = 1883
USERNAME = "ppf_backend"
PASSWORD = "BsW0mmVr5CoDAzW21ibADB7t-kM"
TOPIC = "workshop/1/pit/10/sensors"

payload = {
    "device_id": "ESP32-PLACEHOLDER",
    "license_key": "LIC-608Z-5442-TXXP",
    "temperature": 27.5,
    "humidity": 55.0,
}

client = mqtt.Client(client_id="test-publisher", clean_session=True)
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 10)
client.loop_start()
time.sleep(1)

result = client.publish(TOPIC, json.dumps(payload), qos=1)
result.wait_for_publish()
print(f"Published to {TOPIC}: {payload}")
print(f"RC: {result.rc}")

time.sleep(2)
client.loop_stop()
client.disconnect()
print("Done")
