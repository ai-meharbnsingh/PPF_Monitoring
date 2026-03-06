# Raspberry Pi Fleet - Master Configuration

> Single source of truth for all Pi devices, sensors, services, and flashing instructions.
> **Last Updated:** 2026-03-06 | **Next Device Number:** piwifi4

---

## 1. Device Registry

| # | Hostname | MAC Address | IP (DHCP) | SD Card | Status | Purpose |
|---|----------|-------------|-----------|---------|--------|---------|
| 1 | `piwifi` | `88:a2:9e:69:f1:3f` | 192.168.29.115 | 32GB | ONLINE | Camera streaming + WiFi portal + Sensors |
| 2 | `piwifi2` | `88:a2:9e:bc:7d:22` | 192.168.29.68 | 32GB | ONLINE | Camera streaming + WiFi portal |
| 3 | `piwifi3` | `88:a2:9e:bc:81:50` | 192.168.29.212 | 32GB | ONLINE | Camera streaming + WiFi portal |

### Credentials (all devices)

| Field | Value |
|-------|-------|
| **Username** | `pi` |
| **Password** | `raspberry` |
| **SSH** | `ssh pi@<IP>` or `ssh pi@<hostname>.local` |

---

## 2. Network Topology

```
Internet
    |
[Router 192.168.29.1] (Jio/Airtel, MAC 6c:c2:42)
    |
    +--- 192.168.29.3   ESP32 Sensor     (MAC c8:f0:9e:9a:8f:9c)
    +--- 192.168.29.64  Mac Studio       (MAC 66:ab:3b) [was Hikvision camera IP]
    +--- 192.168.29.68  piwifi2          (MAC 88:a2:9e:bc:7d:22)
    +--- 192.168.29.115 piwifi           (MAC 88:a2:9e:69:f1:3f)
    +--- 192.168.29.157 CP Plus Camera   (MAC 28:18:fd, password unknown)
    +--- 192.168.29.173 Laptop           (MAC e0:d4:e8)
    +--- 192.168.29.236 Mac Studio (alt) (MAC 66:ab:3b)
```

**WiFi:** SSID `Jas_Mehar` / Password `airtel2730`

---

## 3. Services Installed (Per Device)

Every device gets these services via cloud-init on first boot:

| Service | Port | systemd Unit | Description |
|---------|------|-------------|-------------|
| **SSH** | 22 | `ssh.service` | Remote access |
| **WiFi Portal** | 8080 | `wifi-portal.service` | Web UI to scan/change WiFi |
| **MediaMTX** | 8554/8888/8889/8890/1935 | `mediamtx.service` | Camera RTSP/HLS/WebRTC streaming |
| **Avahi (mDNS)** | 5353 | `avahi-daemon.service` | `<hostname>.local` resolution |
| **Tailscale** | - | `tailscaled.service` | VPN tunnel (installed separately) |

### MediaMTX Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 8554 | RTSP | Camera input/output |
| 1935 | RTMP | RTMP streaming |
| 8888 | HLS | HTTP Live Streaming (used by Tailscale Funnel) |
| 8889 | WebRTC | Low-latency browser playback |
| 8890 | SRT | SRT protocol |

### Service Management Commands

```bash
# Check all services
sudo systemctl status mediamtx wifi-portal avahi-daemon

# Restart a service
sudo systemctl restart mediamtx

# View logs
sudo journalctl -u mediamtx -f
sudo journalctl -u wifi-portal -f

# Enable/disable on boot
sudo systemctl enable mediamtx
sudo systemctl disable mediamtx
```

---

## 4. File Locations (On Each Pi)

```
/home/pi/
├── wifi-portal/
│   ├── wifi_server.py          # Flask WiFi config portal
│   ├── venv/                   # Python virtual environment
│   └── server.log
│
├── mediamtx-server/
│   ├── mediamtx                # MediaMTX binary (v1.11.3, arm64)
│   ├── mediamtx.yml            # Stream config (camera RTSP source)
│   └── mediamtx.log
│
└── setup.log                   # Cloud-init completion log

/etc/systemd/system/
├── wifi-portal.service
└── mediamtx.service

/boot/firmware/
├── config.txt                  # Hardware config (UART, I2C, etc.)
├── cmdline.txt                 # Kernel boot params
├── user-data                   # Cloud-init (runs on first boot only)
├── network-config              # WiFi/Ethernet netplan
└── meta-data                   # Instance ID
```

---

## 5. Camera Configuration

### Hikvision DS-2CD1023G0-I (PoE Camera)

| Field | Value |
|-------|-------|
| **Model** | DS-2CD1023G0-I (2MP, 1080p) |
| **Username** | `admin` |
| **Password** | `Hik@12345` |
| **Power** | PoE required (regular LAN won't power it) |
| **RTSP Main** | `rtsp://admin:Hik@12345@<CAMERA_IP>:554/Streaming/Channels/101` |
| **RTSP Sub** | `rtsp://admin:Hik@12345@<CAMERA_IP>:554/Streaming/Channels/102` |
| **Old IP** | 192.168.29.64 (now reassigned to Mac Studio) |
| **Status** | BLOCKED - needs PoE injector/switch to power on |

### MediaMTX Config (mediamtx.yml)

```yaml
logLevel: info
logDestinations: [stdout, file]
logFile: /home/pi/mediamtx-server/mediamtx.log

rtsp: yes
rtspAddress: :8554
rtspTransport: tcp
rtspEncryption: no

rtmp: yes
rtmpAddress: :1935

hls: yes
hlsAddress: :8888
hlsAllowOrigin: '*'
hlsAlwaysRemux: yes

webrtc: yes
webrtcAddress: :8889
webrtcAllowOrigin: '*'
webrtcEncryption: no

srt: yes
srtAddress: :8890

paths:
  cam1:
    source: rtsp://admin:Hik@12345@<CAMERA_IP>:554/Streaming/Channels/101
    sourceProtocol: tcp
    sourceOnDemand: no
    sourceOnDemandStartTimeout: 10s
    sourceOnDemandCloseAfter: 10s
  cam1-sub:
    source: rtsp://admin:Hik@12345@<CAMERA_IP>:554/Streaming/Channels/102
    sourceProtocol: tcp
    sourceOnDemand: no
```

> Replace `<CAMERA_IP>` with the actual camera IP after powering it with PoE.

### Stream Access URLs (per device)

| Protocol | URL Pattern |
|----------|-------------|
| WebRTC | `http://<PI_IP>:8889/cam1/whep` |
| HLS | `http://<PI_IP>:8888/cam1/index.m3u8` |
| RTSP | `rtsp://<PI_IP>:8554/cam1` |
| Sub-stream | Replace `cam1` with `cam1-sub` for 360p |

---

## 6. Sensor Wiring (GPIO Pinout)

### Raspberry Pi 40-Pin Header

```
        3V3  (1)  (2)  5V
      GPIO2  (3)  (4)  5V      ← PMS5003 VCC
      GPIO3  (5)  (6)  GND     ← PMS5003 GND
      GPIO4  (7)  (8)  GPIO14  ← PMS5003 RX (Pi TX)
        GND  (9)  (10) GPIO15  ← PMS5003 TX (Pi RX)
     GPIO17 (11)  (12) GPIO18
     GPIO27 (13)  (14) GND
     GPIO22 (15)  (16) GPIO23
        3V3 (17)  (18) GPIO24  ← BME688 VCC
     GPIO10 (19)  (20) GND     ← BME688 SDA (Software I2C bus 3)
      GPIO9 (21)  (22) GPIO25  ← BME688 SCL (Software I2C bus 3)
     GPIO11 (23)  (24) GPIO8
        GND (25)  (26) GPIO7   ← BME688 GND
        SDA (27)  (28) SCL
      GPIO5 (29)  (30) GND
      GPIO6 (31)  (32) GPIO12
     GPIO13 (33)  (34) GND
     GPIO19 (35)  (36) GPIO16
     GPIO26 (37)  (38) GPIO20
        GND (39)  (40) GPIO21
```

### BME688 (Temperature, Humidity, Pressure, Gas/IAQ)

| BME688 Pin | Connect To | Pi Pin | GPIO |
|------------|-----------|--------|------|
| VCC | 3.3V | Pin 17 | - |
| SDA | Software I2C SDA | Pin 19 | GPIO10 |
| SCL | Software I2C SCL | Pin 21 | GPIO9 |
| GND | Ground | Pin 25 | - |

**Software config required:**
- `/boot/firmware/config.txt`: add `dtoverlay=i2c-gpio,bus=3,sda=10,scl=9`
- Device node: `/dev/i2c-3`
- Verify: `sudo i2cdetect -y 3` (should show address 0x76 or 0x77)

### PMS5003 (Particulate Matter / PM2.5)

| PMS5003 Pin | Connect To | Pi Pin | GPIO |
|-------------|-----------|--------|------|
| VCC | 5V | Pin 4 | - |
| GND | Ground | Pin 6 | - |
| RX (input) | Pi TX | Pin 8 | GPIO14 |
| TX (output) | Pi RX | Pin 10 | GPIO15 |

**Software config required:**
- `/boot/firmware/config.txt`: add `enable_uart=1`
- Device node: `/dev/serial0` (links to `/dev/ttyS0`)

### Sensor Service (pi-sensors)

```bash
# Install sensor dependencies
pip install bme680 pyserial paho-mqtt

# Service file: /etc/systemd/system/pi-sensors.service
# Script: /home/pi/wifi-portal/pi_sensor_mqtt.py
# MQTT Topic: workshop/<WORKSHOP_ID>/pit/<PIT_ID>/sensors
# Device ID: PIWIFI-XX (matches hostname number)

# Management
sudo systemctl status pi-sensors
sudo systemctl restart pi-sensors
sudo journalctl -u pi-sensors -f
```

### Sensor MQTT Payload Format

```json
{
    "device_id": "PIWIFI-01",
    "license_key": "LIC-MOCK-PI-2026",
    "sensor_type": "BME688+PMS5003",
    "temperature": 24.50,
    "humidity": 55.20,
    "pressure": 1013.25,
    "gas_resistance": 50000,
    "iaq": 50,
    "pm25": 12,
    "timestamp": "2026-03-06T16:53:45Z"
}
```

---

## 7. Tailscale / Remote Access

| Field | Value |
|-------|-------|
| **piwifi Tailscale IP** | 100.113.142.8 |
| **Funnel URL** | `https://piwifi.taile42746.ts.net` |
| **Funnel target** | `http://localhost:8888` (HLS) |
| **Account** | ai.meharbansingh@ |

### Setup Tailscale on a new Pi

```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Login (opens browser URL)
sudo tailscale up

# Get VPN IP
tailscale ip -4

# Enable Funnel (public HTTPS access to HLS)
sudo tailscale funnel --bg --https=443 http://localhost:8888
```

### MQTT Broker (HiveMQ Cloud)

| Field | Value |
|-------|-------|
| **Host** | `c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud` |
| **Port** | 8883 (TLS) |
| **Username** | `ppf_backend` |
| **Password** | `PPF@Mqtt2026!secure` |

---

## 8. How to Flash a New Device

### Step 1: Flash the SD Card

1. Download **Raspberry Pi OS Lite (64-bit)** from https://www.raspberrypi.com/software/
2. Use **Raspberry Pi Imager** to flash it to a microSD card (32GB recommended)
3. Don't bother with Imager's customization (it often doesn't persist)

### Step 2: Configure the Boot Partition

After flashing, the SD card will mount as `bootfs` on your Mac. Run these commands, replacing `N` with the next device number from the registry above:

```bash
# 1. Enable SSH
touch /Volumes/bootfs/ssh

# 2. Write network config
cat > /Volumes/bootfs/network-config << 'EOF'
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true
      optional: true
  wifis:
    wlan0:
      dhcp4: true
      regulatory-domain: "IN"
      access-points:
        "Jas_Mehar":
          password: "airtel2730"
      optional: true
EOF

# 3. Write meta-data (unique instance ID)
cat > /Volumes/bootfs/meta-data << EOF
instance-id: rpi-imager-piwifiN
EOF

# 4. Write config.txt (UART + I2C for sensors)
cat > /Volumes/bootfs/config.txt << 'EOF'
dtparam=i2c_arm=on
dtparam=audio=on
camera_auto_detect=1
display_auto_detect=1
auto_initramfs=1
dtoverlay=vc4-kms-v3d
max_framebuffers=2
disable_fw_kms_setup=1
arm_64bit=1
disable_overscan=1
arm_boost=1

[cm4]
otg_mode=1

[cm5]
dtoverlay=dwc2,dr_mode=host

[all]
enable_uart=1
dtoverlay=i2c-gpio,bus=3,sda=10,scl=9
EOF
```

### Step 3: Write the user-data (cloud-init)

This is the big one. It installs all packages, creates all services, and downloads MediaMTX on first boot.

Generate the password hash first:
```bash
openssl passwd -6 'raspberry'
```

Then write the user-data file. **You must change these values:**
- `hostname: piwifiN` (replace N)
- `HOSTNAME = 'piwifiN'` (in wifi_server.py section)
- `hostnamectl set-hostname piwifiN` (in runcmd section)
- The `passwd:` field (use the hash from above)

The full user-data template is identical to what's on `piwifi` (device #1). SSH into it and copy:

```bash
# Copy user-data from the reference device
sshpass -p 'raspberry' ssh pi@192.168.29.115 "cat /boot/firmware/user-data" > /Volumes/bootfs/user-data

# Then find-and-replace the hostname:
sed -i '' 's/piwifi\b/piwifiN/g' /Volumes/bootfs/user-data
sed -i '' "s/HOSTNAME = 'piwifi'/HOSTNAME = 'piwifiN'/" /Volumes/bootfs/user-data
```

Or use the full user-data from the repo's `raspberrypi_config/old/` reference files.

### Step 4: Eject and Boot

```bash
# Safely eject (WAIT for this to complete)
diskutil eject /dev/diskX
```

1. Insert SD card into Pi
2. Power on
3. Wait 3-5 minutes (cloud-init installs packages + downloads MediaMTX)
4. Find the Pi: `ping piwifiN.local` or scan the network

### Step 5: Verify

```bash
# SSH in
ssh pi@piwifiN.local

# Check services
sudo systemctl status mediamtx wifi-portal avahi-daemon

# Check cloud-init completed
cat ~/setup.log

# If sensors are connected, install sensor service (see Section 6)
```

### Step 6: Update This Registry

After the device is online, update the **Device Registry** table in Section 1:
- Fill in the MAC address: `ip link show wlan0 | grep ether`
- Fill in the DHCP IP
- Set status to ONLINE
- Update **Next Device Number** at the top of this file

---

## 9. Troubleshooting

### Pi won't connect to WiFi
```bash
# Check if NetworkManager is running
sudo systemctl status NetworkManager

# Manually connect
sudo nmcli device wifi connect "Jas_Mehar" password "airtel2730" ifname wlan0

# Check WiFi interface
ip link show wlan0
iwconfig wlan0
```

### Services not starting after first boot
```bash
# Check if cloud-init finished
cloud-init status
cat /var/log/cloud-init-output.log | tail -50

# Manually enable and start
sudo systemctl daemon-reload
sudo systemctl enable mediamtx wifi-portal
sudo systemctl start mediamtx wifi-portal
```

### MediaMTX can't reach camera
```bash
# Test camera connectivity
ping <CAMERA_IP>

# Test RTSP directly
ffmpeg -rtsp_transport tcp -i "rtsp://admin:Hik@12345@<CAMERA_IP>:554/Streaming/Channels/101" -t 2 -f null -

# Check MediaMTX logs
sudo journalctl -u mediamtx -f
```

### Can't find Pi on network
```bash
# From your Mac, scan the network
arp -a | grep "88:a2:9e"

# Or use nmap
nmap -sn 192.168.29.0/24

# Or ping the mDNS name
ping piwifiN.local
```

### SD card corruption
```bash
# On Pi, check filesystem
sudo dmesg | grep -i "error\|corrupt\|readonly"
df -h
sudo fsck -n /dev/mmcblk0p2

# If read-only, reboot. If persistent, reflash the SD card.
```

---

## 10. Adding a New Sensor

To add a new sensor type to a Pi:

### 1. Wire the sensor (refer to Section 6 pinout)

### 2. Create/modify the sensor script

```bash
# On the Pi
nano /home/pi/wifi-portal/pi_sensor_mqtt.py
```

Add the new sensor reading logic. The script must output JSON matching the payload format in Section 6.

### 3. Install any required Python packages

```bash
cd /home/pi/wifi-portal
source venv/bin/activate
pip install <new-sensor-library>
```

### 4. Create/update the systemd service

```bash
sudo tee /etc/systemd/system/pi-sensors.service << 'EOF'
[Unit]
Description=Pi Sensor MQTT Publisher
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wifi-portal
ExecStart=/home/pi/wifi-portal/venv/bin/python /home/pi/wifi-portal/pi_sensor_mqtt.py
Restart=always
RestartSec=10
Environment="MQTT_BROKER=c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud"
Environment="MQTT_PORT=8883"
Environment="MQTT_USERNAME=ppf_backend"
Environment="MQTT_PASSWORD=PPF@Mqtt2026!secure"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pi-sensors
sudo systemctl start pi-sensors
```

### 5. Verify data is flowing

```bash
# Check logs
sudo journalctl -u pi-sensors -f

# Check backend received data
curl https://ppf-backend-w0aq.onrender.com/api/health
```

---

## 11. Quick Reference Card

### SSH into any Pi
```bash
ssh pi@piwifi.local      # Device 1
ssh pi@piwifi2.local     # Device 2
ssh pi@piwifi3.local     # Device 3
# Password: raspberry
```

### Check all services
```bash
sudo systemctl status mediamtx wifi-portal avahi-daemon
```

### View camera stream
```
http://<PI_IP>:8889/cam1/whep        # WebRTC (low latency)
http://<PI_IP>:8888/cam1/index.m3u8  # HLS (compatible)
```

### WiFi Portal
```
http://<PI_IP>:8080
```

### Reboot
```bash
sudo reboot
```

### System health
```bash
uptime && free -h && df -h
```
