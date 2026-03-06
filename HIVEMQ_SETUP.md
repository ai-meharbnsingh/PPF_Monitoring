# HiveMQ Cloud Setup for Online Deployment

## Step 1: Create HiveMQ Cloud Account (FREE)
1. Go to: https://console.hivemq.cloud/
2. Sign up with your email
3. Create a new cluster (Free tier)
4. Wait for cluster to be ready (2-3 minutes)

## Step 2: Get Credentials
From your HiveMQ dashboard, copy:
- **Cluster URL**: something like `xxx.s1.eu.hivemq.cloud`
- **Port**: `8883` (MQTTS/TLS)
- **Username**: your-username
- **Password**: your-password

## Step 3: Update Pi Sensor Script

SSH into PiWiFi and update the script:

```bash
ssh pi@192.168.29.115

cd ~/sensor_scripts
nano pi_sensor_mqtt.py
```

Update these lines:
```python
# OLD (local):
MQTT_BROKER = '192.168.29.115'
MQTT_PORT = 1883
MQTT_USERNAME = ''
MQTT_PASSWORD = ''
MQTT_USE_TLS = False

# NEW (HiveMQ Cloud):
MQTT_BROKER = 'YOUR_CLUSTER_URL.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_USERNAME = 'your-username'
MQTT_PASSWORD = 'your-password'
MQTT_USE_TLS = True
```

## Step 4: Update Backend Environment

Add to backend/.env:
```bash
# HiveMQ Cloud (for online deployment)
MQTT_BROKER_HOST=YOUR_CLUSTER_URL.s1.eu.hivemq.cloud
MQTT_BROKER_PORT=8883
MQTT_USERNAME=your-username
MQTT_PASSWORD=your-password
MQTT_USE_TLS=true
```

## Step 5: Deploy Backend

Deploy backend to Railway/Render with these environment variables.

## Result
✅ Pi sends data to HiveMQ Cloud
✅ Backend receives from anywhere
✅ All 3 pits show real sensor data
✅ 60s lag sync still works
