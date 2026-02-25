# Frontend Audit Test Plan — PPF Monitoring System

> **Purpose:** Complete manual test checklist for auditing the live frontend.
> Covers every tab, form, button, role, and workflow end-to-end.
> **Total Test Actions: 167**

**Roles tested:** `super_admin` | `owner` | `staff` | `customer (public)`

---

## Pre-requisites (Before Starting)

1. Docker stack is running (`docker compose up -d`)
2. Backend healthy at `http://localhost:8000/health`
3. Frontend running at `http://localhost:5173`
4. Super admin seeded (`super_admin / SuperAdmin@123`)
5. Hikvision camera online at `192.168.29.64`
6. ESP32 sending data via MQTT (mobile hotspot)

---

## PHASE 1: SUPER ADMIN — Full Platform Setup (28 tests)

### A. Login (Login Page)
- [ ] 1. Open `http://localhost:5173` → verify redirect to `/login`
- [ ] 2. Try login with **wrong password** → verify error message appears
- [ ] 3. Try login with **empty fields** → verify validation
- [ ] 4. Login as `super_admin / SuperAdmin@123` → verify redirect to Dashboard
- [ ] 5. Verify sidebar shows: Dashboard, Jobs, Alerts, Devices, Staff, **Admin**

### B. Admin Panel — Workshop Management (`/admin`)
- [ ] 6. Click **Admin** tab in sidebar
- [ ] 7. See the existing workshops list (or empty state)
- [ ] 8. **Create Workshop**: Fill name, slug, email, phone → click "Create Workshop"
- [ ] 9. Verify workshop appears in the list
- [ ] 10. Try creating a **duplicate slug** → verify error handling

### C. Admin Panel — Pit Management (`/admin`)
- [ ] 11. **Create Pit**: Select the workshop you just created
- [ ] 12. Fill pit number (e.g. `1`), name, description
- [ ] 13. Enter camera IP: `192.168.29.64`
- [ ] 14. Enter RTSP URL: `rtsp://admin:Hik@12345@192.168.29.64:554/Streaming/Channels/102`
- [ ] 15. Click "Create Pit" → verify success toast
- [ ] 16. Try creating a **duplicate pit number** in same workshop → verify error

### D. Staff Management (`/staff`)
- [ ] 17. Click **Staff** tab in sidebar
- [ ] 18. Verify empty state (no staff yet) or existing list
- [ ] 19. Click **"Add Staff"** button
- [ ] 20. Fill: username, password (8+ chars, 1 uppercase, 1 digit), first name, last name, email, phone
- [ ] 21. Click "Create" → verify staff appears in list
- [ ] 22. Verify staff card shows: name, role badge, active badge, username
- [ ] 23. Create a **second staff member** (for later assignment tests)
- [ ] 24. Click **"Reset Password"** on one staff → verify temp password modal appears
- [ ] 25. Note the temporary password shown

### E. Create an Owner User (`/staff`)
- [ ] 26. Click **"Add Staff"** again
- [ ] 27. Create a user with **owner** role
- [ ] 28. Note the owner credentials for Phase 2

---

## PHASE 2: OWNER ROLE — Workshop Operations (93 tests)

### F. Login as Owner
- [ ] 29. **Logout** from super_admin (click logout button)
- [ ] 30. Login as the **owner** you created
- [ ] 31. Verify sidebar shows: Dashboard, Jobs, Alerts, Devices, Staff (but **no Admin tab**)

### G. Dashboard (`/dashboard`)
- [ ] 32. Verify dashboard shows pit cards for the workshop
- [ ] 33. Verify each pit card shows: name, online/offline status, sensor tiles
- [ ] 34. Click **"Refresh"** button → verify data updates
- [ ] 35. Verify "Last updated" timestamp updates
- [ ] 36. Click on a **pit card** → verify navigation to pit detail page

### H. Pit Detail Page (`/pits/:pitId`)
- [ ] 37. Verify **live sensor readings** card (temperature, humidity, PM2.5, PM10)
- [ ] 38. Verify **sensor history chart** is displayed
- [ ] 39. Click chart range buttons: **1h, 6h, 24h, 7d** → verify chart updates
- [ ] 40. Verify **live video feed** is playing (WebRTC or HLS)
- [ ] 41. Verify camera **"Online"** badge and protocol label (WEBRTC/HLS)
- [ ] 42. Verify **sensor overlays on video**: temperature, humidity, PM2.5, IAQ cards
- [ ] 43. Verify **"LIVE"** indicator is pulsing
- [ ] 44. Verify **device online/offline** badge
- [ ] 45. Click **back button** → returns to dashboard

### I. Device Registration (`/devices`)
- [ ] 46. Click **Devices** tab in sidebar
- [ ] 47. Verify empty state or existing devices
- [ ] 48. Click **"Register"** button
- [ ] 49. Fill: Device ID (`ESP32-083AF2A9F084`), select Pit, primary sensor (DHT22), air quality sensor (PMS5003), report interval
- [ ] 50. Click submit → verify **success screen with License Key**
- [ ] 51. **Copy/note the license key** (shown once)
- [ ] 52. Click "Done" → verify device appears in list
- [ ] 53. Verify device card shows: ID, status, pit name, sensor types, last seen
- [ ] 54. Try registering **same device ID again** → verify error

### J. Device Commands (`/devices`)
- [ ] 55. Click **"Command"** button on a device card
- [ ] 56. Select **ENABLE** → click Send → verify success toast
- [ ] 57. Open command modal → select **DISABLE** → verify red button → Send
- [ ] 58. Open command modal → select **SET_INTERVAL** → verify interval input appears → set value → Send
- [ ] 59. Open command modal → select **RESTART** → Send → verify success
- [ ] 60. Try sending command with a **reason** filled in

### K. Job Creation (`/jobs`)
- [ ] 61. Click **Jobs** tab in sidebar
- [ ] 62. Verify empty state or existing jobs list
- [ ] 63. Click **"New Job"** button
- [ ] 64. Fill required fields: select Pit, select Work Type (Full PPF)
- [ ] 65. Fill car details: model, plate, color
- [ ] 66. Fill customer info: name, phone, email
- [ ] 67. Fill price, estimated duration, internal notes
- [ ] 68. Click submit → verify job appears in list
- [ ] 69. Verify job card shows: car model, plate, status (Waiting), work type, price
- [ ] 70. Create a **second job** (Ceramic Coating)
- [ ] 71. Create a **third job** (Partial PPF) — for status transition testing

### L. Job Status Filters (`/jobs`)
- [ ] 72. Click **"All"** tab → verify all jobs shown
- [ ] 73. Click **"Waiting"** tab → verify only waiting jobs
- [ ] 74. Click **"In Progress"** tab → verify empty (none started yet)
- [ ] 75. Verify **pagination** works (page info display)

### M. Job Detail & Status Transitions (`/jobs/:jobId`)
- [ ] 76. Click on a job card → navigate to job detail page
- [ ] 77. Verify: vehicle info, status badge, work type, price, duration, dates
- [ ] 78. Verify **status flow pipeline** visual (4 steps)
- [ ] 79. Verify **customer info** sidebar card
- [ ] 80. Verify **tracking link** card with copy button
- [ ] 81. Click **"Copy Tracking Link"** → verify clipboard copy + check icon
- [ ] 82. Click **"→ In Progress"** → verify status changes, timeline updates
- [ ] 83. Verify **status history timeline** shows the transition
- [ ] 84. Click **"→ Quality Check"** → verify status updates
- [ ] 85. Click **"→ Completed"** → verify job marked done
- [ ] 86. Open **another job** → transition to **"Cancelled"** → verify cancel flow
- [ ] 87. Verify completed/cancelled jobs have **no further transition buttons**

### N. Staff Assignment to Jobs (`/jobs/:jobId`)
- [ ] 88. Open an active (in_progress) job detail
- [ ] 89. Scroll to **Staff Assignment** card (sidebar)
- [ ] 90. Verify checkbox list of active staff members
- [ ] 91. **Check one or more staff** → click "Save Assignment"
- [ ] 92. Verify assignment persists (reload page, staff still checked)
- [ ] 93. **Uncheck a staff member** → save → verify removed

### O. Alerts System (`/alerts`)
- [ ] 94. Click **Alerts** tab in sidebar
- [ ] 95. Verify alert list (may be empty if no threshold breaches)
- [ ] 96. If alerts exist: verify type, severity badge, timestamp, message
- [ ] 97. Click **"Check" (acknowledge)** on an alert → verify "Ack"
- [ ] 98. Click **bell icon** in topbar → verify **alert panel slides in**
- [ ] 99. Verify unread count badge on bell icon
- [ ] 100. Click **"Ack All"** in panel → verify all acknowledged
- [ ] 101. Click outside panel / X button → verify panel closes

### P. Alert Configuration (`/alerts/config`)
- [ ] 102. Click **"Configure"** button on Alerts page
- [ ] 103. Verify current threshold values are loaded
- [ ] 104. **Edit temperature** min/max → Save → verify success toast
- [ ] 105. **Edit humidity** max → Save
- [ ] 106. **Edit PM2.5** warning & critical thresholds → Save
- [ ] 107. **Edit PM10** warning & critical thresholds → Save
- [ ] 108. **Edit IAQ** warning & critical values → Save
- [ ] 109. **Edit device offline** threshold (seconds) → Save
- [ ] 110. Click **Back** → return to Alerts page
- [ ] 111. Re-enter config → verify values persisted

### Q. Customer Tracking (Public)
- [ ] 112. From a job detail page, **copy the tracking link**
- [ ] 113. Open a **new browser tab / incognito window**
- [ ] 114. Paste tracking URL → verify page loads **without login**
- [ ] 115. Verify: vehicle info, status badge, status flow pipeline
- [ ] 116. Verify: scheduled time, actual start, estimated completion
- [ ] 117. Verify **time remaining countdown** is displayed and updating
- [ ] 118. Verify **auto-refresh** (wait 60s or watch network tab)
- [ ] 119. If job completed → verify **"Your car is ready!"** green banner
- [ ] 120. If job cancelled → verify **red cancellation banner**
- [ ] 121. Try a **fake/invalid token** → verify "Job not found" message

---

## PHASE 3: STAFF ROLE — Limited Access (21 tests)

### R. Login as Staff
- [ ] 122. Logout from owner
- [ ] 123. Login as **staff member** (use temp password from step 25)
- [ ] 124. If temp password → verify **redirect to Change Password page**
- [ ] 125. Enter current (temp) password + new password (8+ chars, 1 upper, 1 digit) + confirm
- [ ] 126. Submit → verify redirect to dashboard

### S. Staff Permissions Check
- [ ] 127. Verify sidebar shows: Dashboard, Jobs, Alerts only (**no Devices, Staff, Admin**)
- [ ] 128. Navigate to `/devices` in URL → verify **blocked/redirected**
- [ ] 129. Navigate to `/staff` in URL → verify blocked
- [ ] 130. Navigate to `/admin` in URL → verify blocked

### T. Staff — Dashboard & Pits
- [ ] 131. Verify dashboard shows pit cards (same workshop)
- [ ] 132. Click pit card → verify pit detail loads
- [ ] 133. Verify live video is visible (staff can see video)
- [ ] 134. Verify sensor data displays correctly

### U. Staff — Job Operations
- [ ] 135. Go to Jobs page → verify jobs are visible
- [ ] 136. Verify **"New Job" button is visible** (staff can create jobs)
- [ ] 137. Open a job in "In Progress" status
- [ ] 138. Click **status transition button** → verify staff can update status
- [ ] 139. Verify staff **cannot see Staff Assignment** section

### V. Staff — Alerts (Read Only Config)
- [ ] 140. Go to Alerts page → verify alerts are visible
- [ ] 141. Verify **"Configure" button is NOT visible**
- [ ] 142. Verify staff **can acknowledge** individual alerts

---

## PHASE 4: EDGE CASES & ERROR HANDLING (14 tests)

### W. Network & Offline Scenarios
- [ ] 143. **Disconnect ESP32** (turn off hotspot) → watch for "Offline" badge
- [ ] 144. Verify **device offline alert** is generated
- [ ] 145. Reconnect ESP32 → verify status returns to "Online"
- [ ] 146. **Disconnect camera** (unplug LAN) → verify "Camera Offline"
- [ ] 147. Reconnect camera → verify video resumes

### X. Form Validation
- [ ] 148. Create job with **no pit selected** → verify validation error
- [ ] 149. Create staff with **weak password** ("abc") → verify validation
- [ ] 150. Create staff with **duplicate username** → verify error
- [ ] 151. Set alert threshold with **negative/non-numeric** values → verify handling

### Y. Session & Auth
- [ ] 152. Let session idle → verify **token refresh** works (no random logouts)
- [ ] 153. Two tabs open → logout in one → verify other redirects to login
- [ ] 154. Access protected page while logged out → verify redirect to login with return URL
- [ ] 155. After login → verify redirect back to original page
- [ ] 156. **Manual refresh (Cmd+R / F5)** while filling a form (e.g. halfway through "New Job") → verify if form data is lost or preserved, and session stays alive
- [ ] 157. **Manual refresh on Pit Detail page** → verify video reconnects and sensor data resumes

### Z. Pagination & Empty States
- [ ] 158. Many jobs → verify **pagination prev/next** buttons work
- [ ] 159. Filter jobs to status with **zero results** → verify empty state
- [ ] 160. Devices page with **no devices** → verify empty state + CTA button
- [ ] 161. Staff page with **no staff** → verify empty state + CTA button
- [ ] 162. If search bar exists on Jobs/Alerts → try **special characters** (`<script>`, `%`, `'OR 1=1`) → verify no crash/XSS
- [ ] 163. Try **partial search** (e.g. first 3 letters of car model) → verify results match

### AA. Browser Navigation
- [ ] 164. On Job Detail page → click **browser Back button** → verify returns to Jobs list (not blank page)
- [ ] 165. Then click **browser Forward button** → verify returns to Job Detail with correct data
- [ ] 166. On Pit Detail → browser Back → verify returns to Dashboard with pit cards intact
- [ ] 167. Navigate Dashboard → Pit → Job → Alerts rapidly using **browser Back/Forward** → verify no stale state or crashes
- [ ] 168. Deep-link directly to a Job Detail URL (paste in address bar) → verify page loads correctly without navigating through list first

---

## PHASE 5: RESPONSIVE DESIGN (7 tests)

### BB. Mobile / Tablet Viewport
- [ ] 169. Resize browser to **mobile width (375px)** → verify **Dashboard pit cards** stack vertically
- [ ] 170. Verify **sidebar collapses** to hamburger menu on mobile
- [ ] 171. Open hamburger → verify all nav items accessible → tap to navigate
- [ ] 172. Verify **Tracking page** (public customer page) is fully readable on mobile — this is the most likely page customers access on phone
- [ ] 173. Verify **Job cards** on Jobs list don't overflow on mobile
- [ ] 174. Verify **Pit Detail page**: sensor cards stack, video player scales, chart is scrollable/responsive
- [ ] 175. Resize to **tablet width (768px)** → verify 2-column layouts adapt gracefully

---

## PHASE 6: LIVE DATA VERIFICATION (8 tests)

### CC. Real-Time Sensor Data
- [ ] 176. Pit detail page → verify sensor values are **changing** (not static)
- [ ] 177. Values **match MQTT data** (cross-check with `mosquitto_sub`)
- [ ] 178. History chart **adds new data points** over time
- [ ] 179. **Status colors** change when sensor crosses threshold

### DD. Live Video Feed
- [ ] 180. Pit detail with camera → verify **video is streaming** (not frozen)
- [ ] 181. **Wave hand in front of camera** → verify movement on screen
- [ ] 182. **Sensor overlays on video** update in real-time
- [ ] 183. Test **WebRTC → HLS fallback** (disable one to test)

---

## Summary

| Phase | Role | Tests | Focus |
|-------|------|-------|-------|
| 1 | super_admin | 28 | Platform setup, workshops, pits, staff |
| 2 | owner | 93 | Full operations, jobs, devices, alerts, tracking |
| 3 | staff | 21 | Limited access, permissions, basic operations |
| 4 | edge cases | 20 | Validation, auth, pagination, navigation, refresh |
| 5 | responsive | 7 | Mobile/tablet viewport, hamburger menu, scaling |
| 6 | live data | 8 | Real-time sensors, video, MQTT verification |
| **Total** | | **183** | |
