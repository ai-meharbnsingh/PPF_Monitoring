# Raspberry Pi Configuration Guide

> **Complete setup guide for Raspberry Pi as WiFi Configuration Portal + Camera Streaming Server**
> 
> **Pi IP Address:** `192.168.29.115`  
> **Pi Hostname:** `piwifi.local`  
> **Default Password:** `raspberry`

---

## Table of Contents

1. [Overview](#overview)
2. [WiFi Configuration Portal](#wifi-configuration-portal)
3. [Camera Streaming Server (MediaMTX)](#camera-streaming-server-mediamtx)
4. [File Locations](#file-locations)
5. [Management Commands](#management-commands)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Your Raspberry Pi is configured with two main services:

| Service | Purpose | Port | URL |
|---------|---------|------|-----|
| **WiFi Portal** | Configure WiFi connections | 8080 | http://192.168.29.115:8080 |
| **MediaMTX** | Stream camera feed | 8889 | http://192.168.29.115:8889 |

**Current Network Status:**
- **Connected SSID:** `netplan-wlan0-Jas_Mehar`
- **IP Address:** `192.168.29.115`
- **Hostname:** `piwifi.local`
- **Interface:** `wlan0`

---

## WiFi Configuration Portal

### Access the Portal

Open your browser and navigate to:
```
http://192.168.29.115:8080
```

Or using the hostname:
```
http://piwifi.local:8080
```

### Features

| Feature | Description |
|---------|-------------|
| 🔍 **Scan Networks** | See all available WiFi networks with signal strength |
| 🔐 **Connect** | Enter password and connect to any network |
| 📍 **New IP Display** | Shows the new IP after connecting (handles IP changes) |
| 🔄 **Real-time Status** | Live connection progress updates |
| 📋 **Copy IP** | One-click copy of new IP address |
| 🔌 **Disconnect** | Disconnect from current network |
| 🔄 **Reboot** | Restart the Raspberry Pi remotely |

### How to Change WiFi Network

1. **Open the portal:** http://192.168.29.115:8080
2. **Click "Scan for Networks"**
3. **Select the WiFi network** you want to join
4. **Enter the password** (if required)
5. **Click "Connect"**
6. **Wait for connection:** The page will show progress
7. **See the new IP:** After connection, the new IP is displayed

> ⚠️ **Important:** After connecting to a new network, the IP address will change. Use the displayed new IP or `piwifi.local:8080` to reconnect.

### Available Networks (as of last scan)

| Network | Signal | Security |
|---------|--------|----------|
| Airtel_JasMeharAirtel | 100% | WPA2 |
| Jas_Mehar | 80% | WPA2 |
| Airtel_vino_7851 | 75% | WPA2 |
| Suga_Kookie | 72% | WPA2 |
| JioFiber-4G | 69% | WPA2 |

---

## Camera Streaming Server (MediaMTX)

MediaMTX is running on the Raspberry Pi, pulling the RTSP stream from your Hikvision camera and making it available via multiple protocols.

### Camera Details

| Setting | Value |
|---------|-------|
| **Camera IP** | 192.168.29.64 |
| **Camera Model** | Hikvision DS-2CD1023G0-I (2 MP) |
| **Resolution** | 1920x1080 (1080p) |
| **RTSP URL** | `rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/101` |

### Streaming Endpoints

| Protocol | Endpoint | Use Case |
|----------|----------|----------|
| **WebRTC (Primary)** | `http://192.168.29.115:8889/cam1/whep` | Low latency browser playback |
| **HLS (Fallback)** | `http://192.168.29.115:8888/cam1/index.m3u8` | Compatible with all browsers |
| **RTSP Output** | `rtsp://192.168.29.115:8554/cam1` | For VLC or other RTSP players |
| **Sub-stream (360p)** | `http://192.168.29.115:8889/cam1-sub/whep` | Lower bandwidth option |

### All MediaMTX Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 8554 | RTSP | Camera input / RTSP output |
| 1935 | RTMP | RTMP streaming |
| 8888 | HLS | HTTP Live Streaming |
| 8889 | WebRTC | WebRTC playback |
| 8890 | SRT | SRT protocol |

### Testing the Stream

**Via Browser (HTML Viewer):**
```
http://localhost:8080/camera-viewer.html
```
(From your laptop's test folder)

**Via VLC:**
```
rtsp://192.168.29.115:8554/cam1
```

**Via Browser (WebRTC):**
```
http://192.168.29.115:8889/cam1/whep
```

---

## File Locations

### On Raspberry Pi (/home/pi/)

```
/home/pi/
├── wifi-portal/                    # WiFi Configuration Portal
│   ├── wifi_server.py              # Main Flask server
│   ├── requirements.txt            # Python dependencies
│   ├── server.log                  # Server logs
│   ├── venv/                       # Python virtual environment
│   └── templates/
│       └── wifi_portal.html        # Web interface
│
├── mediamtx-server/                # MediaMTX Streaming Server
│   ├── mediamtx                    # MediaMTX binary
│   ├── mediamtx.yml                # Configuration file
│   └── mediamtx.log                # Server logs
│
└── ...
```

### On Your Laptop (Local)

```
PP_Monitoring/
├── wifi-portal/                    # Source files
│   ├── wifi_server_v2.py
│   ├── wifi_server.py
│   ├── requirements.txt
│   ├── install.sh
│   └── templates/
│       ├── wifi_portal_v2.html
│       └── wifi_portal.html
│
├── test/
│   └── camera-viewer.html          # Camera viewer page
│
├── raspberrypi_config/             # This documentation
│   └── raspberry_config_setup.md   # This file
│
└── ...
```

---

## Management Commands

### SSH Access

```bash
# Connect to Pi
ssh pi@192.168.29.115
# Password: raspberry

# Or with sshpass
sshpass -p "raspberry" ssh pi@192.168.29.115
```

### WiFi Portal Management

```bash
# Check if portal is running
ps aux | grep wifi_server

# View logs
tail -f ~/wifi-portal/server.log

# Restart portal
pkill -f wifi_server
sleep 2
cd ~/wifi-portal
nohup ./venv/bin/python wifi_server.py > server.log 2>&1 &

# Stop portal
pkill -f wifi_server

# Check API status
curl http://localhost:8080/api/status

# Scan networks via API
curl http://localhost:8080/api/scan
```

### MediaMTX Management

```bash
# Check if MediaMTX is running
ps aux | grep mediamtx

# View logs
tail -f ~/mediamtx-server/mediamtx.log

# Restart MediaMTX
pkill mediamtx
sleep 1
cd ~/mediamtx-server
nohup ./mediamtx ./mediamtx.yml > mediamtx.log 2>&1 &

# Stop MediaMTX
pkill mediamtx

# Test RTSP stream
vlc rtsp://localhost:8554/cam1
```

### System Management

```bash
# Check system status
uptime
free -h
df -h

# Check network
ip addr show
iwconfig

# Check WiFi connection
nmcli connection show --active
nmcli device status

# Reboot
sudo reboot

# Shutdown
sudo shutdown now
```

### Service Auto-Start Setup

To make services start automatically on boot:

```bash
# WiFi Portal auto-start
sudo tee /etc/systemd/system/wifi-portal.service << 'EOF'
[Unit]
Description=WiFi Configuration Portal
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wifi-portal
ExecStart=/home/pi/wifi-portal/venv/bin/python /home/pi/wifi-portal/wifi_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable wifi-portal
sudo systemctl start wifi-portal

# MediaMTX auto-start
sudo tee /etc/systemd/system/mediamtx.service << 'EOF'
[Unit]
Description=MediaMTX Streaming Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mediamtx-server
ExecStart=/home/pi/mediamtx-server/mediamtx /home/pi/mediamtx-server/mediamtx.yml
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mediamtx
sudo systemctl start mediamtx

# Check service status
sudo systemctl status wifi-portal
sudo systemctl status mediamtx
```

---

## Troubleshooting

### WiFi Portal Issues

| Problem | Solution |
|---------|----------|
| Portal not loading | Check if server is running: `ps aux \| grep wifi_server` |
| Cannot scan networks | Ensure WiFi interface is up: `sudo ip link set wlan0 up` |
| Connection fails | Check password and signal strength |
| New IP not showing | Wait 10-30 seconds for DHCP assignment |
| mDNS not working | Install avahi: `sudo apt install avahi-daemon` |

### MediaMTX Issues

| Problem | Solution |
|---------|----------|
| No video stream | Check camera IP: `ping 192.168.29.64` |
| Stream lags | Lower camera bitrate or use sub-stream |
| Cannot connect | Check firewall: `sudo iptables -L` |
| High CPU usage | Use sub-stream (360p) instead of main stream |

### Network Issues

| Problem | Solution |
|---------|----------|
| Pi not reachable | Check power and WiFi connection |
| IP changed | Use `piwifi.local` or check router DHCP table |
| Camera not found | Verify camera IP and network connection |
| Slow stream | Check WiFi signal strength and interference |

### Useful Debug Commands

```bash
# Check all listening ports
sudo ss -tlnp

# Check WiFi signal strength
iwconfig

# Check routing table
ip route

# Check DNS resolution
nslookup piwifi.local

# Check camera connectivity
ping 192.168.29.64

# Monitor network traffic
sudo tcpdump -i wlan0 port 8554

# Check system logs
sudo journalctl -f
```

---

## Quick Reference

### URLs Summary

| Service | URL |
|---------|-----|
| WiFi Portal | http://192.168.29.115:8080 |
| WiFi Portal (hostname) | http://piwifi.local:8080 |
| Camera WebRTC | http://192.168.29.115:8889/cam1/whep |
| Camera HLS | http://192.168.29.115:8888/cam1/index.m3u8 |
| Camera RTSP | rtsp://192.168.29.115:8554/cam1 |

### Credentials

| System | Username | Password |
|--------|----------|----------|
| Raspberry Pi | pi | raspberry |
| Hikvision Camera | admin | Hik@12345 |

### Network Configuration

| Device | IP Address | Purpose |
|--------|------------|---------|
| Raspberry Pi | 192.168.29.115 | WiFi Portal + Stream Server |
| Hikvision Camera | 192.168.29.64 | Camera Feed Source |
| Your Laptop | 192.168.29.173 | Access Point |
| Router/Gateway | 192.168.29.1 | Network Gateway |

---

## Notes

- The Raspberry Pi is configured to use `piwifi.local` as its mDNS hostname
- MediaMTX automatically pulls the camera stream via RTSP
- WiFi Portal handles IP changes and shows the new IP after connection
- Both services run on boot if systemd services are enabled
- The camera password is stored in the MediaMTX configuration file

---

*Last Updated: March 3, 2026*  
*Setup by: Kimi CLI*  
*Raspberry Pi Model: Unknown (aarch64)*  
*OS: Raspberry Pi OS (Debian 13)*
