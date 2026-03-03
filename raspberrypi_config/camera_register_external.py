#!/usr/bin/env python3
"""
Camera Registration with External Access Support
Supports ngrok tunnels, cloud servers, or public IPs
"""

import json
import time
import socket
import subprocess
import paho.mqtt.client as mqtt
import os
import requests
from datetime import datetime

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.29.173')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'ppf_backend')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'your_mqtt_password')

# Camera Configuration
CAMERA_ID = os.getenv('CAMERA_ID', 'pi_camera_01')
CAMERA_NAME = os.getenv('CAMERA_NAME', 'Raspberry Pi Camera 1')
WORKSHOP_ID = os.getenv('WORKSHOP_ID', '1')

# EXTERNAL ACCESS CONFIGURATION
# Choose ONE of the following:

# Option 1: Use ngrok tunnel
USE_NGROK = os.getenv('USE_NGROK', 'false').lower() == 'true'
NGROK_API_URL = 'http://localhost:4040/api/tunnels'  # ngrok local API

# Option 2: Use public IP (with port forwarding)
USE_PUBLIC_IP = os.getenv('USE_PUBLIC_IP', 'false').lower() == 'true'
PUBLIC_IP = os.getenv('PUBLIC_IP', '')  # Your router's public IP

# Option 3: Use cloud relay server
USE_CLOUD_RELAY = os.getenv('USE_CLOUD_RELAY', 'false').lower() == 'true'
CLOUD_RELAY_HOST = os.getenv('CLOUD_RELAY_HOST', '')  # e.g., your-app.fly.dev

# Option 4: Use Tailscale/VPN IP
USE_TAILSCALE = os.getenv('USE_TAILSCALE', 'false').lower() == 'true'
TAILSCALE_IP = os.getenv('TAILSCALE_IP', '')  # 100.x.x.x

# Local MediaMTX ports
LOCAL_IP = os.getenv('LOCAL_IP', '192.168.29.115')
MEDIAMTX_PORTS = {
    'webrtc': 8889,
    'hls': 8888,
    'rtsp': 8554,
    'rtmp': 1935
}


def get_ngrok_urls():
    """Get public URLs from ngrok API"""
    try:
        resp = requests.get(NGROK_API_URL, timeout=5)
        data = resp.json()
        
        urls = {}
        for tunnel in data.get('tunnels', []):
            proto = tunnel.get('proto', '')  # https or http
            public_url = tunnel.get('public_url', '')
            local_addr = tunnel.get('config', {}).get('addr', '')
            
            # Map based on local port
            if ':8889' in local_addr:
                urls['webrtc'] = public_url.replace('https://', 'wss://').replace('http://', 'ws://')
            elif ':8888' in local_addr:
                urls['hls'] = public_url
        
        return urls
    except Exception as e:
        print(f"Failed to get ngrok URLs: {e}")
        return {}


def get_public_ip():
    """Get public IP address"""
    try:
        resp = requests.get('https://api.ipify.org?format=json', timeout=5)
        return resp.json().get('ip', '')
    except:
        return PUBLIC_IP


def get_stream_urls():
    """Generate stream URLs based on configuration"""
    
    if USE_NGROK:
        # Use ngrok tunnel URLs
        ngrok_urls = get_ngrok_urls()
        return {
            'webrtc': {'main': ngrok_urls.get('webrtc', ''), 'sub': ''},
            'hls': {'main': ngrok_urls.get('hls', ''), 'sub': ''},
            'note': 'via ngrok tunnel'
        }
    
    elif USE_PUBLIC_IP:
        # Use public IP with port forwarding
        public_ip = get_public_ip() or PUBLIC_IP
        return {
            'webrtc': {
                'main': f"http://{public_ip}:{MEDIAMTX_PORTS['webrtc']}/cam1/whep",
                'sub': f"http://{public_ip}:{MEDIAMTX_PORTS['webrtc']}/cam1-sub/whep"
            },
            'hls': {
                'main': f"http://{public_ip}:{MEDIAMTX_PORTS['hls']}/cam1/index.m3u8",
                'sub': f"http://{public_ip}:{MEDIAMTX_PORTS['hls']}/cam1-sub/index.m3u8"
            },
            'note': f'via public IP {public_ip}'
        }
    
    elif USE_CLOUD_RELAY:
        # Use cloud relay server ( Pi pushes to cloud )
        return {
            'webrtc': {
                'main': f"https://{CLOUD_RELAY_HOST}/cam1/whep",
                'sub': f"https://{CLOUD_RELAY_HOST}/cam1-sub/whep"
            },
            'hls': {
                'main': f"https://{CLOUD_RELAY_HOST}/cam1/index.m3u8",
                'sub': f"https://{CLOUD_RELAY_HOST}/cam1-sub/index.m3u8"
            },
            'note': f'via cloud relay {CLOUD_RELAY_HOST}'
        }
    
    elif USE_TAILSCALE:
        # Use Tailscale VPN IP
        # Try to auto-detect Tailscale IP if not provided
        if not TAILSCALE_IP:
            try:
                import subprocess
                result = subprocess.run(['tailscale', 'ip', '-4'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    TAILSCALE_IP = result.stdout.strip()
                    print(f"✓ Auto-detected Tailscale IP: {TAILSCALE_IP}")
            except:
                pass
        
        ip = TAILSCALE_IP or LOCAL_IP
        return {
            'webrtc': {
                'main': f"http://{ip}:8889/cam1/whep",
                'sub': f"http://{ip}:8889/cam1-sub/whep"
            },
            'hls': {
                'main': f"http://{ip}:8888/cam1/index.m3u8",
                'sub': f"http://{ip}:8888/cam1-sub/index.m3u8"
            },
            'rtsp': {
                'main': f"rtsp://{ip}:8554/cam1",
                'sub': f"rtsp://{ip}:8554/cam1-sub"
            },
            'note': f'via Tailscale VPN {ip}'
        }
    
    else:
        # Default: Local network only
        return {
            'webrtc': {
                'main': f"http://{LOCAL_IP}:8889/cam1/whep",
                'sub': f"http://{LOCAL_IP}:8889/cam1-sub/whep"
            },
            'hls': {
                'main': f"http://{LOCAL_IP}:8888/cam1/index.m3u8",
                'sub': f"http://{LOCAL_IP}:8888/cam1-sub/index.m3u8"
            },
            'rtsp': {
                'main': f"rtsp://{LOCAL_IP}:8554/cam1",
                'sub': f"rtsp://{LOCAL_IP}:8554/cam1-sub"
            },
            'note': 'local network only'
        }


class CameraRegistrar:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"camera_{CAMERA_ID}")
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
            self.connected = True
            self.register_camera()
        else:
            print(f"❌ Connection failed: {rc}")
            self.connected = False
    
    def register_camera(self):
        if not self.connected:
            return
        
        stream_urls = get_stream_urls()
        
        camera_info = {
            'device_id': CAMERA_ID,
            'name': CAMERA_NAME,
            'type': 'raspberry_pi',
            'ip_address': LOCAL_IP,
            'workshop_id': WORKSHOP_ID,
            'status': 'online',
            'is_online': True,
            'capabilities': {
                'resolutions': ['1920x1080', '640x360'],
                'protocols': ['webrtc', 'hls', 'rtsp'],
                'has_audio': False,
                'has_ptz': False
            },
            'stream_urls': stream_urls,
            'access_note': stream_urls.get('note', ''),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        topic = f"workshop/{WORKSHOP_ID}/cameras/register"
        self.client.publish(topic, json.dumps(camera_info), qos=1)
        
        print("\n📡 Camera registered!")
        print(f"   Device ID: {CAMERA_ID}")
        print(f"   WebRTC: {stream_urls.get('webrtc', {}).get('main', 'N/A')}")
        print(f"   Access: {stream_urls.get('note', 'local')}")
    
    def run(self):
        print("=" * 60)
        print("Camera Registration (with External Access)")
        print("=" * 60)
        
        if USE_NGROK:
            print("Mode: Ngrok Tunnel")
        elif USE_PUBLIC_IP:
            print("Mode: Public IP (port forwarding)")
        elif USE_CLOUD_RELAY:
            print("Mode: Cloud Relay")
        elif USE_TAILSCALE:
            print("Mode: Tailscale VPN")
        else:
            print("Mode: Local Network Only")
        
        print("=" * 60)
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            
            # Keep running
            while True:
                time.sleep(30)
                # Re-register to update URLs (ngrok may change)
                if USE_NGROK:
                    self.register_camera()
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == '__main__':
    registrar = CameraRegistrar()
    registrar.run()
