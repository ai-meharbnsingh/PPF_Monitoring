# PP Monitoring — Next Steps

## Live Deployment (Completed)
- [x] Frontend on Vercel: https://ppf-monitoring.vercel.app
- [x] Backend on Render: https://ppf-backend-w0aq.onrender.com
- [x] PostgreSQL on Render (database: ppf_monitoring)
- [x] Cron ping to keep backend alive
- [x] CORS configured for Vercel origin
- [x] Super admin seeded (super_admin / SuperAdmin@123)

## MQTT Cloud Setup (Completed)
- [x] Set up HiveMQ Cloud (free tier) — c4cb4d2b4a3e432c9d61b8b56ee359af.s1.eu.hivemq.cloud
- [x] Create MQTT credentials (ppf_backend / PPF@Mqtt2026!secure)
- [x] Update Render env vars (MQTT_BROKER_HOST, PORT=8883, USE_TLS=true)
- [x] TLS support added in backend code (mqtt_service.py) + ESP32 firmware (WiFiClientSecure)
- [x] Update ESP32 firmware config.h to point to HiveMQ Cloud broker
- [x] Firmware builds successfully with TLS changes (58.6% flash, 16.4% RAM)
- [x] Flash ESP32 with updated firmware
- [x] ESP32 connected & publishing to HiveMQ Cloud (confirmed via serial monitor)
- [x] Backend connects to HiveMQ Cloud (TLS, single worker, unique client ID)
- [x] Device registered in Render DB (ESP32-083AF2A9F084 / LIC-A4RE-38HN-GVL2)
- [x] Workshop 15, Pit 10, Subscription created in Render DB
- [x] Fixed MQTT disconnect loop (Dockerfile: 2 workers → 1 worker)
- [x] Fixed unique MQTT client ID per process (PID + UUID suffix)
- [x] Reflash ESP32 to clear DISABLED state (close serial monitor first, then `pio run -t upload`)
- [x] Verify end-to-end: sensor_data table populated → WebSocket → Vercel frontend

## Pipeline Status (Verified 2026-02-26)
ESP32 (BME680) → HiveMQ Cloud (MQTT/TLS:8883) → Render Backend → PostgreSQL → WebSocket → Vercel Frontend
- All 8 stages passing: Health, MQTT→DB, Device, Pit API, Frontend, Stats, WebSocket live push, Auth
- 180+ sensor readings in DB, ~10s interval
- Device: ESP32-083AF2A9F084, Pit 10, Workshop 15

## Pending — Priority Order

### P0: Quick Wins (< 1 hour each)
- [ ] Fix pre-existing TypeScript errors (`tsc` fails, `vite build` works) — clean up type issues
- [ ] Custom domain — add via Vercel dashboard + Render settings (just DNS config)
- [ ] Commit all P2 changes to GitHub (`git add` + `git push`)
- [ ] Run `alembic upgrade head` on Render DB to apply `pit_alert_configs` migration

### P1: Feature Work (half day each)
- [ ] Book Consultation form — create backend API endpoint + DB table + wire up frontend form
- [ ] Email notifications — configure SMTP in Render env vars, wire up alert triggers in backend
- [ ] CI/CD pipeline — add GitHub Actions for backend (Render already auto-deploys, Vercel too)

### P2: Bigger Effort (done ✅ — 2026-02-26)
- [x] Per-pit alert thresholds — `PitAlertConfig` model + migration + `evaluate_alerts` updated + API routes + PitDetailPage panel
- [x] User management — StaffPage rewritten with role tabs, edit modal, deactivate/activate, owner creation
- [x] Mobile responsive polish — AlertConfigPage + AdminPage responsive grids + dark theme fixes
- [x] MediaMTX documentation — setup guide at `docs/MEDIAMTX_SETUP.md` (local WiFi for now)
- [ ] Multi-device UI — DevicesPage registration/reassignment modal (backend routes exist, frontend pending)

### P3: Nice-to-Have
- [ ] PM2.5/PM10 sensor — add PMS5003 particle sensor to ESP32 (currently null in readings)
- [ ] Historical charts — add time-series graphs on frontend (Chart.js/Recharts)
- [ ] Export data — CSV/PDF download of sensor history
- [ ] OTA firmware updates — ESP32 firmware update via backend (OTA code already in repo)

---

## 🎯 What to Do Next

1. **`git add . && git commit -m "P2: per-pit alerts, user mgmt, mobile polish" && git push`**
2. **Run migration**: `alembic upgrade head` (locally or on Render)
3. **Set MediaMTX env vars** in backend `.env`:
   ```
   MEDIAMTX_HOST=localhost
   MEDIAMTX_RTSP_PORT=8554
   MEDIAMTX_WEBRTC_PORT=8889
   STREAM_TOKEN_SECRET=<any-random-string>
   ```
4. **Test per-pit alerts**: Open a pit → expand "Alert Thresholds" → set an override → verify source badge changes
5. **Test team page**: Go to Team → try role tabs, edit a user, deactivate/activate
6. **Next feature**: Pick from P1 (consultation form, email alerts, CI/CD) or finish multi-device UI

## Key Files
- Frontend Dockerfile: `frontend/Dockerfile`
- Nginx template: `frontend/nginx.conf.template`
- Backend settings: `backend/src/config/settings.py` (accepts DATABASE_URL directly)
- MQTT service: `backend/src/services/mqtt_service.py` (TLS support added)
- Landing page: `frontend/src/pages/PublicSplashPage.tsx`

## Credentials & URLs
- Vercel project: ai-meharbnsinghs-projects/ppf-monitoring
- Render DB external: postgresql://eagle_admin:***@dpg-d5sf3fm3jp1c73erp4gg-a.oregon-postgres.render.com/ppf_monitoring
- GitHub: https://github.com/ai-meharbnsingh/PPF_Monitoring
