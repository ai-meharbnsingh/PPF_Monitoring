# Hikvision Camera Discovery

This document describes how to discover and register Hikvision IP cameras on your local network.

## Overview

The system supports automatic discovery of Hikvision cameras using multiple methods:

1. **ONVIF WS-Discovery** - Standard protocol for IP camera discovery
2. **UPnP/SSDP** - Universal Plug and Play discovery
3. **Network Scanning** - Active scanning of IP ranges

## Quick Start

### Using the Standalone Script

The easiest way to discover cameras is using the standalone script:

```bash
# Quick discovery (ONVIF + SSDP only)
python scripts/discover_hikvision_cameras.py

# Full network scan with auto-detected subnet
python scripts/discover_hikvision_cameras.py --auto-scan

# Scan specific subnet
python scripts/discover_hikvision_cameras.py --subnet 192.168.1.0/24

# Scan IP range
python scripts/discover_hikvision_cameras.py --ip-range 192.168.1.1-192.168.1.100

# Output as JSON
python scripts/discover_hikvision_cameras.py --subnet 192.168.1.0/24 --json

# Output as CSV
python scripts/discover_hikvision_cameras.py --subnet 192.168.1.0/24 --csv
```

### Using the API

#### Discover Cameras (without registering)

```bash
curl -X POST "http://localhost:8000/api/v1/cameras/discover/hikvision?workshop_id=1&auto_scan=true"
```

#### Discover and Auto-Register Cameras

```bash
curl -X POST "http://localhost:8000/api/v1/cameras/discover/hikvision?workshop_id=1&auto_scan=true&register=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Discover with Specific Subnet

```bash
curl -X POST "http://localhost:8000/api/v1/cameras/discover/hikvision?workshop_id=1&subnet=192.168.1.0/24&register=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Response Format

```json
{
  "message": "Hikvision discovery complete",
  "workshop_id": 1,
  "cameras_found": 2,
  "cameras_registered": 2,
  "cameras_existing": 0,
  "cameras": [
    {
      "device_id": "hikvision-192-168-1-100-80",
      "name": "Hikvision Camera (192.168.1.100)",
      "description": "Discovered Hikvision camera via scan",
      "camera_type": "hikvision",
      "model": "DS-2CD1023G0-I",
      "manufacturer": "Hikvision",
      "ip_address": "192.168.1.100",
      "port": 554,
      "mac_address": "00:12:34:56:78:9A",
      "stream_urls": {
        "rtsp": {
          "main": "rtsp://192.168.1.100:554/Streaming/Channels/101"
        },
        "hls": null,
        "webrtc": null
      },
      "protocols": ["rtsp", "http"],
      "has_ptz": false,
      "has_audio": false,
      "is_online": true,
      "firmware_version": "V5.6.0",
      "discovered_via": "scan"
    }
  ],
  "subnet_used": "192.168.1.0/24"
}
```

## Default RTSP URLs

Once cameras are discovered, the default RTSP URLs follow Hikvision's standard format:

```
rtsp://<username>:<password>@<ip>:554/Streaming/Channels/101  (Main stream)
rtsp://<username>:<password>@<ip>:554/Streaming/Channels/102  (Sub stream)
```

Default credentials:
- Username: `admin`
- Password: (empty or device verification code)

## Camera Registration Flow

1. **Discovery Phase**: System scans network for Hikvision cameras
2. **Registration Phase**: Found cameras are added to the database
3. **Assignment Phase**: Cameras are assigned to specific pits

```bash
# Step 1: Discover and register cameras
curl -X POST "http://localhost:8000/api/v1/cameras/discover/hikvision?workshop_id=1&auto_scan=true&register=true"

# Step 2: List unassigned cameras
curl "http://localhost:8000/api/v1/cameras/discovered?workshop_id=1"

# Step 3: Assign camera to a pit
curl -X POST "http://localhost:8000/api/v1/cameras/1/assign" \
  -H "Content-Type: application/json" \
  -d '{"pit_id": 1, "custom_name": "Pit 1 Camera"}'
```

## Troubleshooting

### No Cameras Found

1. **Check network connectivity**:
   ```bash
   ping 192.168.1.64  # Default Hikvision IP
   ```

2. **Verify camera is ONVIF enabled**:
   - Login to camera web interface
   - Go to Configuration → Network → Advanced Settings → Integration Protocol
   - Enable ONVIF

3. **Check firewall settings**:
   - ONVIF uses UDP port 3702
   - HTTP uses port 80
   - RTSP uses port 554

### Camera Found but Can't Stream

1. **Verify RTSP port is open**:
   ```bash
   telnet <camera-ip> 554
   ```

2. **Check camera credentials**:
   - Default: admin/(empty)
   - Newer models use device verification code

3. **Test RTSP URL**:
   ```bash
   ffplay rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
   ```

## Network Requirements

| Protocol | Port | Purpose |
|----------|------|---------|
| ONVIF WS-Discovery | UDP 3702 | Camera discovery |
| SSDP | UDP 1900 | UPnP discovery |
| HTTP | TCP 80, 81, 82, 8000, 8080 | Web interface / API |
| RTSP | TCP 554 | Video streaming |
| HTTPS | TCP 443 | Secure web interface |

## Security Considerations

1. **Change default passwords** after camera registration
2. **Use HTTPS** when accessing camera web interfaces
3. **Enable RTSP authentication** on cameras
4. **Segment camera network** using VLANs if possible

## Integration with MediaMTX

For cameras to be available in the web interface, configure MediaMTX to proxy the RTSP streams:

```yaml
# mediamtx.yml
paths:
  pit1_camera:
    source: rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
    sourceProtocol: tcp
```

See [CAMERA_SETUP.md](CAMERA_SETUP.md) for detailed MediaMTX configuration.
