# Raspberry Pi Configuration

This folder contains all the configuration files and documentation for your Raspberry Pi setup.

## 📁 Files in this Folder

| File | Description |
|------|-------------|
| `raspberry_config_setup.md` | **Complete setup guide** with all details |
| `mediamtx.yml` | MediaMTX streaming server configuration |
| `wifi_server.py` | WiFi Portal Flask server (backup) |
| `README.md` | This file - quick reference |

## 🚀 Quick Start

### Access Your Pi Services

| Service | URL |
|---------|-----|
| **WiFi Portal** | http://192.168.29.115:8080 |
| **WiFi Portal** (hostname) | http://piwifi.local:8080 |
| **Camera Stream** (WebRTC) | http://192.168.29.115:8889/cam1/whep |
| **Camera Stream** (HLS) | http://192.168.29.115:8888/cam1/index.m3u8 |

### SSH Access

```bash
ssh pi@192.168.29.115
# Password: raspberry
```

## 🔄 Restore/Setup Commands

If you need to restore the setup on a fresh Pi:

### 1. WiFi Portal Setup

```bash
# On the Raspberry Pi:
mkdir -p ~/wifi-portal/templates
cd ~/wifi-portal

# Copy files (from this folder via SCP)
# Then install dependencies:
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv network-manager wireless-tools iw

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors werkzeug

# Start server
nohup ./venv/bin/python wifi_server.py > server.log 2>&1 &
```

### 2. MediaMTX Setup

```bash
# On the Raspberry Pi:
mkdir -p ~/mediamtx-server
cd ~/mediamtx-server

# Download MediaMTX
wget https://github.com/bluenviron/mediamtx/releases/download/v1.11.3/mediamtx_v1.11.3_linux_arm64v8.tar.gz
tar -xzf mediamtx_*.tar.gz

# Copy mediamtx.yml from this folder
# Then start:
nohup ./mediamtx ./mediamtx.yml > mediamtx.log 2>&1 &
```

## 📞 Current Status

- **Pi IP:** 192.168.29.115
- **Hostname:** piwifi.local
- **Connected WiFi:** netplan-wlan0-Jas_Mehar
- **Camera IP:** 192.168.29.64

## 📝 Notes

- All services are running and configured
- WiFi Portal automatically shows new IP after network change
- MediaMTX streams camera feed via WebRTC/HLS/RTSP
- mDNS enabled: access via `piwifi.local`

---

For detailed information, see `raspberry_config_setup.md`
