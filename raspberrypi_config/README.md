# Raspberry Pi Configuration & Deployment Guide

> **Complete configuration for Raspberry Pi devices and system deployment**
> 
> **Last Updated:** 2026-03-07

---

## 📁 Files in This Directory

| File | Purpose |
|------|---------|
| `PI_MASTER_CONFIG.md` | Master configuration for all Pi devices (registry, wiring, services) |
| `DEPLOYMENT.md` | Complete deployment guide (Online + Local) |
| `ENVIRONMENT_VARIABLES.md` | Reference for ALL environment variables |
| `DATABASE_SETUP.md` | Database setup including **subscription requirement** |
| `docker-compose.local.yml` | Local development infrastructure (Postgres + MQTT) |
| `pi_sensor_mqtt.py` | Sensor script for Pi (BME688 + PMS5003) |
| `pi-sensors.service` | Systemd service file for sensor script |
| `setup_sensors.sh` | Automated setup script for new Pi devices |
| `old/` | Archived configuration files |

---

## 🚀 Quick Start

### For New Pi Device Setup

1. **Flash SD card** → See `PI_MASTER_CONFIG.md` Section 8
2. **Wire sensors** → See `PI_MASTER_CONFIG.md` Section 6
3. **Run setup script:**
   ```bash
   bash setup_sensors.sh
   ```
4. **Register in database** → See `DATABASE_SETUP.md` (CRITICAL!)

### For Online Deployment

1. **Read:** `DEPLOYMENT.md`
2. **Set environment variables:** `ENVIRONMENT_VARIABLES.md`
3. **Configure database:** `DATABASE_SETUP.md`

### For Local Development

```bash
# 1. Start local infrastructure
cd raspberrypi_config
docker-compose -f docker-compose.local.yml up -d

# 2. Setup backend
cd ../backend
# Follow DEPLOYMENT.md Section 3

# 3. Setup frontend
cd ../frontend
# Follow DEPLOYMENT.md Section 3
```

---

## 🔧 Configuration Files

### Production (Render + Vercel)

| Component | Config File | Variables Location |
|-----------|-------------|-------------------|
| Backend | `../render.yaml` | Render Dashboard |
| Frontend | Vercel Project Settings | Vercel Dashboard |
| Pi | `pi_sensor_mqtt.py` | Hardcoded in script |

### Local Development

| Component | Config File | Variables Location |
|-----------|-------------|-------------------|
| Backend | `../backend/.env` | Environment file |
| Frontend | `../frontend/.env` | Environment file |
| Infrastructure | `docker-compose.local.yml` | Docker Compose |

---

## 📋 Important Checklists

### New Device Checklist

- [ ] SD card flashed with Raspberry Pi OS
- [ ] WiFi configured (SSID: `Jas_Mehar`)
- [ ] Sensors wired correctly (see `PI_MASTER_CONFIG.md` Section 6)
- [ ] `pi_sensor_mqtt.py` configured with correct IDs
- [ ] Service installed and running
- [ ] **Database device record created**
- [ ] **Database subscription record created** ⚠️
- [ ] Data verified in dashboard

### Production Deployment Checklist

- [ ] Neon database created
- [ ] HiveMQ Cloud cluster created
- [ ] Backend deployed to Render
- [ ] Frontend deployed to Vercel
- [ ] All environment variables set
- [ ] CORS origins configured
- [ ] Device registered in database
- [ ] Subscription created in database ⚠️
- [ ] Pi sending data to MQTT
- [ ] Dashboard showing online status

---

## ⚠️ Critical Requirements

### Device Subscription (DO NOT SKIP!)

**For a device to work, BOTH records must exist:**

```sql
-- 1. Device record
INSERT INTO devices (device_id, license_key, status, workshop_id, pit_id)
VALUES ('PIWIFI-01', 'LIC-RG-STUDIO-2026', 'active', 2, 3);

-- 2. Subscription record (REQUIRED!)
INSERT INTO subscriptions (workshop_id, device_id, license_key, plan, status, monthly_fee, currency)
VALUES (2, 'PIWIFI-01', 'LIC-RG-STUDIO-2026', 'trial', 'active', 0, 'INR');
```

**Without the subscription record, sensor data will be rejected!**

See `DATABASE_SETUP.md` for complete instructions.

---

## 🔌 Sensor Wiring Quick Reference

### BME688 (I2C - Pins 3, 5, 9)

| BME688 | Pi Pin | GPIO |
|--------|--------|------|
| VCC | Pin 1 (3.3V) | - |
| SDA | Pin 3 | GPIO2 |
| SCL | Pin 5 | GPIO3 |
| GND | Pin 9 | - |

### PMS5003 (UART - Pins 4, 6, 8, 10)

| PMS5003 | Pi Pin | GPIO |
|---------|--------|------|
| VCC | Pin 4 (5V) | - |
| GND | Pin 6 | - |
| RX | Pin 8 | GPIO14 (TX) |
| TX | Pin 10 | GPIO15 (RX) |

See `PI_MASTER_CONFIG.md` Section 6 for detailed wiring.

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Device shows offline | Check `DATABASE_SETUP.md` - subscription missing? |
| No sensor data | Verify Pi service: `sudo journalctl -u pi-sensors -f` |
| PMS5003 permission error | See `PI_MASTER_CONFIG.md` Section 6 for fix |
| BME688 not detected | Check I2C: `sudo i2cdetect -y 1` |
| Backend 404 | Use correct URL: `ppf-backend-w0aq.onrender.com` |
| CORS errors | Check `CORS_ORIGINS` includes Vercel domain |

---

## 📞 Service URLs

### Production

| Service | URL |
|---------|-----|
| Frontend | https://ppf-monitoring.vercel.app |
| Backend | https://ppf-backend-w0aq.onrender.com |
| Health Check | https://ppf-backend-w0aq.onrender.com/health |
| Pi (Tailscale) | https://piwifi.taile42746.ts.net |

### Local Development

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Backend Docs | http://localhost:8000/docs |
| Database Admin | http://localhost:8080 (Adminer) |

---

## 📚 Documentation Index

| Document | What's Inside |
|----------|---------------|
| `PI_MASTER_CONFIG.md` | Device registry, wiring diagrams, flashing instructions, service management |
| `DEPLOYMENT.md` | Complete deployment for online (Render/Vercel) and local development |
| `ENVIRONMENT_VARIABLES.md` | All environment variables explained with examples |
| `DATABASE_SETUP.md` | SQL scripts for device registration, subscription requirement |

---

## 🔄 Keeping Configuration Updated

When making changes:

1. Update the relevant `.md` file
2. Update `PI_MASTER_CONFIG.md` **Last Updated** date
3. Commit changes:
   ```bash
   git add raspberrypi_config/
   git commit -m "docs: update configuration for X"
   git push
   ```

---

## 🔐 Security Notes

- Change default passwords before production use
- Use strong `JWT_SECRET_KEY` (64+ hex characters)
- Store sensitive credentials in environment variables, NOT in code
- Enable TLS for MQTT in production (`MQTT_USE_TLS=true`)
- Restrict CORS origins to specific domains

---

## 💡 Tips

1. **Always verify database subscription exists** when adding new devices
2. **Use the setup script** `setup_sensors.sh` for consistent Pi configuration
3. **Check Render logs** when backend issues occur
4. **Use Tailscale** for secure remote Pi access
5. **Keep `PI_MASTER_CONFIG.md` updated** with new device information

---

**Need help?** Check the detailed documentation in each `.md` file above.
