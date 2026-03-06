# Cloud Relay Setup - No Tailscale Needed for Owner

> Stream camera through a cloud server so owner can access from web app without installing Tailscale.

---

## 🎯 Goal

**Owner experience:**
1. Opens web app: `https://your-app.vercel.app`
2. Logs in normally
3. Clicks on camera
4. **Stream loads!** ✅

No Tailscale installation needed on owner's device!

---

## 🏗️ Architecture

```
Owner's Browser
      ↓ HTTPS
   Web App (Vercel)
      ↓ WSS/WebRTC
Cloud MediaMTX (Fly.io)
      ↓ RTSP (over internet)
 Raspberry Pi (pushes stream)
      ↓ Local RTSP
  Hikvision Camera
```

**Pi actively PUSHES stream to cloud, owner PULLS from cloud.**

---

## 🔧 Step 1: Deploy Cloud MediaMTX

You already have `fly-mediamtx` folder!

```bash
# From your laptop
cd fly-mediamtx

# Deploy to Fly.io
fly deploy

# Get your cloud URL
fly status
# Output: https://ppf-streams.fly.dev
```

---

## 🔧 Step 2: Configure Pi to Push Stream to Cloud

On Raspberry Pi, install FFmpeg:

```bash
# SSH to Pi
ssh pi@192.168.29.115

# Install FFmpeg
sudo apt-get update
sudo apt-get install -y ffmpeg

# Test pushing stream to cloud
ffmpeg -i rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/101 \
  -c copy -f rtsp \
  rtsp://ppf-streams.fly.dev:8554/cam1
```

If this works, automate it:

---

## 🔧 Step 3: Create Auto-Push Service

```bash
# On Pi, create service
sudo tee /etc/systemd/system/camera-cloud-relay.service << 'EOF'
[Unit]
Description=Camera Cloud Relay
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/ffmpeg \
  -i rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/101 \
  -c copy \
  -f rtsp \
  -rtsp_transport tcp \
  rtsp://ppf-streams.fly.dev:8554/cam1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable camera-cloud-relay
sudo systemctl start camera-cloud-relay
```

---

## 🔧 Step 4: Update Camera Registration

When Pi registers, it should send the **cloud URLs** instead of local URLs:

```python
# In camera_register.py - modify get_stream_urls()

def get_stream_urls(self):
    cloud_host = "ppf-streams.fly.dev"  # Your cloud server
    
    return {
        'webrtc': {
            'main': f"https://{cloud_host}/cam1/whep",
            'sub': f"https://{cloud_host}/cam1-sub/whep"
        },
        'hls': {
            'main': f"https://{cloud_host}/cam1/index.m3u8",
            'sub': f"https://{cloud_host}/cam1-sub/index.m3u8"
        },
        'note': 'via cloud relay'
    }
```

---

## 🌐 Result: Owner Access

Now when owner opens web app:

```javascript
// Frontend gets this URL from backend:
const streamUrl = "https://ppf-streams.fly.dev/cam1/whep"

// VideoPlayer connects directly to cloud
<video src={streamUrl} />

// No Tailscale needed! Works from anywhere!
```

---

## 📊 Comparison: Tailscale vs Cloud Relay

| Feature | Tailscale | Cloud Relay |
|---------|-----------|-------------|
| **Owner needs app?** | ✅ Yes (Tailscale) | ❌ No |
| **Setup complexity** | Easy | Medium |
| **Latency** | Low (~10ms) | Higher (~100ms) |
| **Cost** | Free | ~$5-20/month |
| **Bandwidth** | Unlimited | Limited by cloud |
| **Security** | Very High | High (HTTPS) |
| **Best for** | Team/owners | Customers/public |

---

## 💡 Recommendation

### For Owner/Internal Team:
Use **Tailscale** - secure, free, low latency

### For Customers/Public Access:
Use **Cloud Relay** - no installation needed

### Hybrid Approach (Best!)
```
Owner/Staff → Tailscale → Direct to Pi (low latency, free)
Customers → Cloud Relay → No setup needed
```

---

## 🔌 Quick Commands

### Check if stream is reaching cloud:
```bash
# From any computer
curl https://ppf-streams.fly.dev/cam1/index.m3u8
# Should return playlist, not error
```

### View cloud stream:
```
https://ppf-streams.fly.dev/cam1/whep
```

### Check Pi relay status:
```bash
ssh pi@192.168.29.115
sudo systemctl status camera-cloud-relay
tail -f /var/log/syslog | grep ffmpeg
```

---

## 🎉 Summary

| Scenario | Solution |
|----------|----------|
| Owner on phone, no Tailscale | Use **Cloud Relay** |
| Owner has Tailscale | Use **Tailscale** (better) |
| Multiple owners | **Cloud Relay** easier |
| Just you/admin | **Tailscale** is fine |

**For your use case with owner accessing web app remotely, Cloud Relay is the best solution!**

Would you like me to set up the cloud relay configuration files?
