import paho.mqtt.client as mqtt
import json
import sys

# Configuration - Using Pi's MQTT
MQTT_BROKER = "192.168.29.115"  # Pi IP
MQTT_PORT = 1883
TOPIC = "workshop/1/pit/1/sensors"  # Default topic

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to Pi MQTT ({MQTT_BROKER})")
        print(f"📡 Subscribed to: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print("\n" + "="*50)
        print(f"📥 Received Sensor Data from {data.get('device_id', 'Unknown')}")
        print("="*50)
        
        # Display PM data
        if 'pm1' in data:
            print(f"🌫️  Air Quality:")
            print(f"   PM1.0:  {data['pm1']} μg/m³")
            print(f"   PM2.5:  {data['pm25']} μg/m³")
            print(f"   PM10:   {data['pm10']} μg/m³")
        
        # Display BME688 data
        if 'temperature' in data:
            print(f"🌡️  Environment:")
            print(f"   Temperature: {data['temperature']}°C")
            print(f"   Humidity:    {data['humidity']}%")
            print(f"   Pressure:    {data['pressure']} hPa")
            if 'gas_resistance' in data:
                print(f"   Gas:         {data['gas_resistance']:.0f} Ω")
        
        print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")
        print("="*50)
        
    except Exception as e:
        print(f"Error parsing message: {e}")
        print(f"Raw: {msg.payload.decode()}")

print("🔌 Connecting to Pi MQTT broker...")
print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"   Topic:  {TOPIC}")
print("\nWaiting for sensor data...\n")

client = mqtt.Client(
    client_id="ppf-studio-debug"
)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 10)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n👋 Disconnecting...")
    client.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
