# 🌐 Global Camera Access with Tailscale

> Access your Raspberry Pi camera from **anywhere in the world** securely using Tailscale VPN.

---

## ✅ What You Get

| Before (Local Only) | After (Global with Tailscale) |
|---------------------|-------------------------------|
| ❌ Only on same WiFi | ✅ Access from anywhere |
| ❌ Limited to home/office | ✅ Works globally |
| ❌ Complex port forwarding | ✅ No router config needed |
| ❌ Security risks | ✅ Encrypted WireGuard tunnel |
| ❌ Public IP required | ✅ Works with any internet |

---

## 🗺️ Network Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                │
│                                                                 │
│  ┌──────────────┐         Tailscale Cloud         ┌──────────┐ │
│  │ Your Phone   │◄───────────────────────────────►│   VPN    │ │
│  │ (Anywhere)   │      Encrypted Tunnel           │  Server  │ │
│  │              │                                 │          │ │
│  │ http://      │                                 │          │ │
│  │ 100.x.x.x:8889│                                 │          │ │
│  └──────────────┘                                 └────┬─────┘ │
│                                                        │       │
│  ┌──────────────┐                              ┌──────┴─────┐ │
│  │ Your Laptop  │◄────────────────────────────►│  Raspberry │ │
│  │ (Office)     │      Secure Connection       │     Pi     │ │
│  └──────────────┘                              │  (Camera)  │ │
│                                                └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Tailscale on Raspberry Pi

```bash
# SSH to your Pi
ssh pi@192.168.29.115

# Download and run setup script
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Or use our automated script:
./setup_tailscale.sh
```

You'll see a login URL - open it in your browser and sign in.

### Step 2: Get Your Pi's Tailscale IP

```bash
# On the Pi
tailscale ip -4
# Output: 100.64.x.x (remember this!)
```

### Step 3: Install Tailscale on Your Device

| Device | How to Install |
|--------|---------------|
| **iPhone/iPad** | App Store → Search "Tailscale" |
| **Android** | Play Store → Search "Tailscale" |
| **Windows/Mac** | https://tailscale.com/download |
| **Linux** | `curl -fsSL https://tailscale.com/install.sh \| sh` |

**Important:** Login with the **same account** you used on the Pi!

---

## 🎥 Access Your Camera

Once Tailscale is running on both devices:

### From Web Browser
```
http://100.x.x.x:8889/cam1/whep
```
(Replace 100.x.x.x with your Pi's Tailscale IP)

### From Your App
Go to Cameras page - it will show the camera with the Tailscale URL!

### From VLC Player
```
rtsp://100.x.x.x:8554/cam1
```

---

## 📱 Example: Viewing From Your Phone

1. **Install Tailscale** app on your iPhone
2. **Login** with same account as Pi
3. **Open Safari** and go to:
   ```
   http://100.64.123.45:8889/cam1/whep
   ```
4. **Watch your camera live!** 📹

---

## 🔧 Files Included

| File | Purpose |
|------|---------|
| `setup_tailscale.sh` | Automated Tailscale installation on Pi |
| `tailscale_status.sh` | Shows current status and URLs |
| `camera_register_external.py` | Registers camera with Tailscale IP |
| `TAILSCALE_SETUP.md` | Detailed setup guide |

---

## 📋 Commands Reference

### On Raspberry Pi:

```bash
# Check status
./tailscale_status.sh

# View Tailscale info
tailscale ip -4
sudo tailscale status

# Check if services are running
sudo systemctl status tailscaled
sudo systemctl status camera-register-tailscale

# Restart camera registration
sudo systemctl restart camera-register-tailscale
```

### On Any Device:

```bash
# Connect to Tailscale
sudo tailscale up

# View connected devices
sudo tailscale status

# Disconnect
sudo tailscale down
```

---

## 🔒 Security

- ✅ **WireGuard encryption** - Military-grade security
- ✅ **Private network** - Only your devices can access
- ✅ **No open ports** - Router stays secure
- ✅ **Device authentication** - Every device must login
- ✅ **Free for personal use** - Up to 20 devices

---

## 🐛 Troubleshooting

### Camera not accessible?

```bash
# 1. Check Tailscale is running
sudo tailscale status

# 2. Check your Tailscale IP
tailscale ip -4

# 3. Check MediaMTX is running
ps aux | grep mediamtx

# 4. Test locally first
http://192.168.29.115:8889/cam1/whep

# 5. Then test via Tailscale
http://100.x.x.x:8889/cam1/whep
```

### Can't connect from phone?
- Make sure Tailscale app is **running** (icon in status bar)
- Check you're using the **same login** on phone and Pi
- Verify Pi is online: `ping 100.x.x.x` (from your phone)

---

## 💡 Pro Tips

1. **Bookmark the URL** - Save `http://100.x.x.x:8889/cam1/whep` in your browser

2. **Name your Pi** - In Tailscale admin panel, rename your Pi to "camera-pi"

3. **Enable HTTPS** - Tailscale supports HTTPS for even more security

4. **Share with team** - Add coworkers to your Tailscale network

5. **Check admin panel** - https://login.tailscale.com/admin to manage devices

---

## 📊 Admin Panel

Visit: https://login.tailscale.com/admin

You can:
- See all your devices
- Check who's online
- Remove old devices
- View connection logs
- Configure ACLs (access control)

---

## 🎯 Summary

| Question | Answer |
|----------|--------|
| **Can I see camera from anywhere?** | ✅ YES! With Tailscale |
| **Is it secure?** | ✅ YES! WireGuard encryption |
| **Does it cost money?** | ✅ FREE for personal use |
| **Do I need to open router ports?** | ❌ NO! Tailscale handles it |
| **Works on phone?** | ✅ YES! iOS and Android apps |
| **How many devices?** | ✅ Up to 20 for free |

---

## 🚀 Ready to Start?

```bash
# On Raspberry Pi
ssh pi@192.168.29.115
./setup_tailscale.sh

# Then install Tailscale on your phone
# And access: http://100.x.x.x:8889/cam1/whep
```

**Your camera is now accessible from anywhere in the world! 🌍🎥**

---

*For detailed setup instructions, see: `docs/setup/TAILSCALE_SETUP.md`*
