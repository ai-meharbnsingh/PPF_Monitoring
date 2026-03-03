# Tailscale Setup Guide - Access Camera From Anywhere

> Set up Tailscale VPN to access your Raspberry Pi camera from anywhere in the world securely.

---

## 🌐 What Tailscale Does

```
Without Tailscale (Local Only):
┌─────────────┐      ❌      ┌─────────────┐
│   Your      │   Cannot    │  Raspberry  │
│   Phone     │◄──────────►│     Pi      │
│  (Remote)   │   Access    │  (Camera)   │
└─────────────┘             └─────────────┘
       ↓ Local WiFi only

With Tailscale (Global Access):
┌─────────────┐     ✅      ┌─────────────┐
│   Your      │◄──────────►│  Tailscale  │
│   Phone     │   Secure    │    VPN      │
│  (Anywhere) │   Tunnel    │   Cloud     │
└─────────────┘             └──────┬──────┘
                                   │
                            ┌──────┴──────┐
                            │  Raspberry  │
                            │     Pi      │
                            │  (Camera)   │
                            └─────────────┘
```

**Result:** Access your camera from anywhere as if you were on the same WiFi!

---

## ✅ Prerequisites

- Raspberry Pi with camera setup (already done)
- A Tailscale account (free)
- Device(s) to view camera from (phone/laptop)

---

## 🔧 Step 1: Install Tailscale on Raspberry Pi

### Option A: Using the Setup Script (Recommended)

```bash
# On your laptop, copy the script to Pi
scp raspberrypi_config/setup_tailscale.sh pi@192.168.29.115:/home/pi/

# SSH to Pi and run it
ssh pi@192.168.29.115
chmod +x setup_tailscale.sh
./setup_tailscale.sh
```

### Option B: Manual Installation

```bash
# SSH to Pi
ssh pi@192.168.29.115

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

# You'll see a URL - open it in browser to login
```

---

## 🔐 Step 2: Authenticate (Important!)

After running `sudo tailscale up`, you'll see:

```
To authenticate, visit:

        https://login.tailscale.com/a/xxxxxxxxxxxx
```

1. **Open that URL** in your browser
2. **Sign up/login** with:
   - Google account
   - Microsoft account  
   - GitHub account
   - Or email
3. **Authorize** the Pi

---

## 📱 Step 3: Get Your Pi's Tailscale IP

```bash
# On the Pi
tailscale ip -4
```

You'll get an IP like: `100.x.x.x` (this is your Pi's permanent VPN address)

**Example:**
```
100.64.123.45
```

---

## 📲 Step 4: Install Tailscale on Your Devices

### Windows/Mac
1. Download from: https://tailscale.com/download
2. Install and login with **SAME account** as Pi
3. Done!

### iPhone/iPad
1. Open App Store
2. Search "Tailscale"
3. Install and login

### Android
1. Open Play Store
2. Search "Tailscale"
3. Install and login

### Another Linux Machine
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

---

## 🎥 Step 5: Access Your Camera From Anywhere!

Once Tailscale is running on both Pi and your device:

### Web Browser
```
http://100.x.x.x:8889/cam1/whep
```
(Replace 100.x.x.x with your Pi's Tailscale IP)

### Your App
Go to: `http://100.x.x.x:8080` (WiFi Portal)

### VLC Player
```
rtsp://100.x.x.x:8554/cam1
```

---

## 📋 Complete URL Reference

Replace `100.x.x.x` with your actual Tailscale IP:

| Protocol | URL | Use Case |
|----------|-----|----------|
| **WebRTC** | `http://100.x.x.x:8889/cam1/whep` | Browser (lowest latency) |
| **HLS** | `http://100.x.x.x:8888/cam1/index.m3u8` | Browser (best compatibility) |
| **RTSP** | `rtsp://100.x.x.x:8554/cam1` | VLC, apps |
| **WiFi Portal** | `http://100.x.x.x:8080` | Configure Pi WiFi |

---

## 🔒 Security Features

✅ **Encrypted:** All traffic is WireGuard encrypted  
✅ **Private:** Only devices in your Tailnet can access  
✅ **No port forwarding:** No need to open router ports  
✅ **No public IP:** Works even with CGNAT (mobile networks)  

---

## 🧪 Testing

### Test 1: Check Pi is online
```bash
# On any device with Tailscale
ping 100.x.x.x
```

### Test 2: Check MediaMTX
```bash
# On any device with Tailscale
curl http://100.x.x.x:8889/cam1/whep
# Should return SDP data (not error)
```

### Test 3: View Stream
Open browser: `http://100.x.x.x:8889/cam1/whep`

---

## 🔄 Auto-Start on Boot

The setup script already configures this, but to verify:

```bash
# Check Tailscale is enabled
sudo systemctl is-enabled tailscaled

# Check camera registration is enabled
sudo systemctl is-enabled camera-register-tailscale

# View status
sudo tailscale status
sudo systemctl status camera-register-tailscale
```

---

## 📊 Managing Your Tailscale Network

### Web Admin Panel
Visit: https://login.tailscale.com/admin

You can:
- See all connected devices
- Remove devices
- Enable/disable features
- View connection logs

### CLI Commands
```bash
# View status
sudo tailscale status

# View IP
tailscale ip -4

# Stop Tailscale
sudo tailscale down

# Start Tailscale
sudo tailscale up

# Logout
sudo tailscale logout
```

---

## 🐛 Troubleshooting

### Can't access camera?
```bash
# 1. Check Tailscale is running on Pi
sudo tailscale status

# 2. Check MediaMTX is running
ps aux | grep mediamtx

# 3. Check Tailscale IP
ping $(tailscale ip -4)

# 4. Check ports are listening
sudo ss -tlnp | grep -E '8888|8889'
```

### Device not showing in Tailscale?
- Make sure you logged in with the **SAME account** on all devices
- Check admin panel: https://login.tailscale.com/admin

### Slow connection?
- Try DERP relays: `sudo tailscale up --reset`
- Check if direct connection: `sudo tailscale status` (look for "direct")

---

## 💰 Pricing

| Plan | Cost | Devices | Features |
|------|------|---------|----------|
 **Personal** | **FREE** | Up to 20 devices | All features |
| Starter | $5/mo | Up to 5 users | Shared nodes |
| Business | $15/user/mo | Unlimited | SSO, ACLs |

**For camera streaming: FREE plan is sufficient!**

---

## 🎯 Quick Summary

1. **Install Tailscale on Pi:** `curl -fsSL https://tailscale.com/install.sh | sh`
2. **Login:** `sudo tailscale up` (open URL, authenticate)
3. **Get IP:** `tailscale ip -4` (remember this!)
4. **Install Tailscale on your devices** (same login)
5. **Access camera:** `http://100.x.x.x:8889/cam1/whep`

**Done! Your camera is now accessible from anywhere in the world! 🌍**

---

## 📞 Support

- Tailscale Docs: https://tailscale.com/kb
- Tailscale Community: https://forum.tailscale.com
- Check status: https://status.tailscale.com
