"""
Listen to ALL MQTT topics for 30 seconds and print everything received.
This tells us if the ESP32 is connected and what topic it's publishing on.
"""
import paho.mqtt.client as mqtt
import time

messages = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] Connected to Mosquitto")
        client.subscribe("#", qos=1)  # subscribe to ALL topics
        print("[OK] Subscribed to ALL topics (#)")
    else:
        print(f"[FAIL] Connect RC={rc}")

def on_message(client, userdata, message):
    msg = f"TOPIC: {message.topic} | PAYLOAD: {message.payload.decode('utf-8', errors='replace')}"
    print(msg)
    messages.append(msg)

client = mqtt.Client(client_id="debug-listener", clean_session=True)
client.username_pw_set("ppf_backend", "BsW0mmVr5CoDAzW21ibADB7t-kM")
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 10)
client.loop_start()

print("Listening for 20 seconds for ANY MQTT message...")
time.sleep(20)
client.loop_stop()
client.disconnect()

if not messages:
    print("\nNO MESSAGES RECEIVED — ESP32 is not connected to MQTT or hotspot")
else:
    print(f"\nReceived {len(messages)} messages total")
