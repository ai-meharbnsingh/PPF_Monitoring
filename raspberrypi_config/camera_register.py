#!/usr/bin/env python3
"""
Camera Registration Service for Raspberry Pi
Registers camera with backend via MQTT when connected to network
"""

import json
import time
import socket
import subprocess
import paho.mqtt.client as mqtt
import os
from datetime import datetime

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.29.173')  # Your laptop/backend IP
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'ppf_backend')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'your_mqtt_password')

# Camera Configuration
CAMERA_ID = os.getenv('CAMERA_ID', 'pi_camera_01')
CAMERA_NAME = os.getenv('CAMERA_NAME', 'Raspberry Pi Camera 1')
WORKSHOP_ID = os.getenv('WORKSHOP_ID', '1')  # Default workshop ID

# MediaMTX Stream URLs
MEDIAMTX_HOST = os.getenv('MEDIAMTX_HOST', 'localhost')
MEDIAMTX_PORTS = {
    'webrtc': 8889,
    'hls': 8888,
    'rtsp': 8554,
    'rtmp': 1935
}

STREAM_PATHS = ['cam1', 'cam1-sub']


class CameraRegistrar:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"camera_{CAMERA_ID}")
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        self.connected = False
        self.last_ping = 0
        
    def get_ip_address(self):
        """Get current IP address"""
        try:
            # Get IP from wlan0
            result = subprocess.run(
                ["ip", "addr", "show", "wlan0"],
                capture_output=True, text=True
            )
            for line in result.stdout.split('\n'):
                if 'inet ' in line:
                    return line.split()[1].split('/')[0]
        except:
            pass
        
        # Fallback
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_hostname(self):
        """Get device hostname"""
        return socket.gethostname()
    
    def get_stream_urls(self, ip=None):
        """Generate stream URLs"""
        if not ip:
            ip = self.get_ip_address()
        
        return {
            'webrtc': {
                'main': f"http://{ip}:{MEDIAMTX_PORTS['webrtc']}/cam1/whep",
                'sub': f"http://{ip}:{MEDIAMTX_PORTS['webrtc']}/cam1-sub/whep"
            },
            'hls': {
                'main': f"http://{ip}:{MEDIAMTX_PORTS['hls']}/cam1/index.m3u8",
                'sub': f"http://{ip}:{MEDIAMTX_PORTS['hls']}/cam1-sub/index.m3u8"
            },
            'rtsp': {
                'main': f"rtsp://{ip}:{MEDIAMTX_PORTS['rtsp']}/cam1",
                'sub': f"rtsp://{ip}:{MEDIAMTX_PORTS['rtsp']}/cam1-sub"
            },
            'rtmp': {
                'main': f"rtmp://{ip}:{MEDIAMTX_PORTS['rtmp']}/cam1",
                'sub': f"rtmp://{ip}:{MEDIAMTX_PORTS['rtmp']}/cam1-sub"
            }
        }
    
    def get_camera_info(self):
        """Get complete camera info"""
        ip = self.get_ip_address()
        hostname = self.get_hostname()
        
        return {
            'device_id': CAMERA_ID,
            'name': CAMERA_NAME,
            'type': 'raspberry_pi',
            'ip_address': ip,
            'hostname': f"{hostname}.local",
            'workshop_id': WORKSHOP_ID,
            'status': 'online',
            'capabilities': {
                'resolutions': ['1920x1080', '640x360'],
                'protocols': ['webrtc', 'hls', 'rtsp', 'rtmp'],
                'has_audio': False,
                'has_ptz': False
            },
            'stream_urls': self.get_stream_urls(ip),
            'mediamtx_config': {
                'host': ip,
                'ports': MEDIAMTX_PORTS,
                'paths': STREAM_PATHS
            },
            'timestamp': datetime.utcnow().isoformat(),
            'firmware_version': '1.0.0'
        }
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {MQTT_BROKER}")
            self.connected = True
            # Register camera immediately
            self.register_camera()
        else:
            print(f"❌ Failed to connect, return code: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        print(f"⚠️ Disconnected from MQTT broker (rc: {rc})")
        self.connected = False
    
    def on_publish(self, client, userdata, mid):
        print(f"📤 Message published (mid: {mid})")
    
    def register_camera(self):
        """Send camera registration message"""
        if not self.connected:
            print("⚠️ Not connected to MQTT, cannot register")
            return
        
        camera_info = self.get_camera_info()
        topic = f"workshop/{WORKSHOP_ID}/cameras/register"
        payload = json.dumps(camera_info)
        
        result = self.client.publish(topic, payload, qos=1, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📡 Camera registered: {CAMERA_ID}")
            print(f"   IP: {camera_info['ip_address']}")
            print(f"   WebRTC: {camera_info['stream_urls']['webrtc']['main']}")
        else:
            print(f"❌ Failed to register camera")
    
    def send_heartbeat(self):
        """Send periodic heartbeat"""
        if not self.connected:
            return
        
        heartbeat = {
            'device_id': CAMERA_ID,
            'status': 'online',
            'ip_address': self.get_ip_address(),
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': time.time()
        }
        
        topic = f"workshop/{WORKSHOP_ID}/cameras/heartbeat"
        self.client.publish(topic, json.dumps(heartbeat), qos=0)
        print(f"💓 Heartbeat sent")
    
    def send_status_update(self, status='online'):
        """Send status update"""
        if not self.connected:
            return
        
        update = {
            'device_id': CAMERA_ID,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        topic = f"workshop/{WORKSHOP_ID}/cameras/status"
        self.client.publish(topic, json.dumps(update), qos=1)
        print(f"📊 Status update: {status}")
    
    def run(self):
        """Main loop"""
        print("=" * 60)
        print("Camera Registration Service")
        print("=" * 60)
        print(f"Camera ID: {CAMERA_ID}")
        print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Workshop: {WORKSHOP_ID}")
        print("=" * 60)
        
        try:
            # Connect to MQTT
            print(f"🔗 Connecting to MQTT broker...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(1)
                timeout -= 1
            
            if not self.connected:
                print("❌ Could not connect to MQTT broker")
                return
            
            # Main loop - send heartbeat every 30 seconds
            print("\n⏳ Running... (Press Ctrl+C to stop)")
            while True:
                time.sleep(30)
                self.send_heartbeat()
                
                # Re-register if IP changed
                # (This would check if IP changed and re-register)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            self.send_status_update('offline')
            self.client.loop_stop()
            self.client.disconnect()
            print("👋 Disconnected")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == '__main__':
    registrar = CameraRegistrar()
    registrar.run()
