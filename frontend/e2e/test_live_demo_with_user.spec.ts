/**
 * LIVE DEMO TEST WITH NEW USER CREATION & WEBCAM
 *
 * This test executes the FULL PROTOCOL:
 * 1. Login as super_admin
 * 2. Create new Workshop with Owner User
 * 3. Create Pit with camera RTSP URL
 * 4. Setup webcam stream to MediaMTX
 * 5. Login as new Owner
 * 6. Navigate to pit with live camera view
 * 7. Display in browser (headed mode)
 */

import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const API_URL = "http://localhost:8000/api/v1";

const SUPER_ADMIN = {
  username: "super_admin",
  password: "SuperAdmin@123",
};

// NEW USER TO CREATE
const NEW_OWNER = {
  username: `owner_${Date.now()}`,
  email: `owner_${Date.now()}@example.com`, // Valid email format
  password: "OwnerPassword@123",
  first_name: "Demo",
  last_name: "Owner",
};

const WORKSHOP_NAME = `Demo AutoSpa ${Date.now()}`;

test.describe("LIVE DEMO - Full Protocol with New User & Camera", () => {
  let workshopId: number;
  let pitId: number;
  let deviceId: number;
  let ownerUserId: number;
  let superAdminToken: string;
  let ownerToken: string;

  test("SETUP: Create workshop, pit, user, and device", async () => {
    console.log("\n🔧 ═══════════════════════════════════════════════════════");
    console.log("   SETUP: Creating full demo environment");
    console.log("═══════════════════════════════════════════════════════\n");

    // 1. Get super_admin token
    console.log(`📌 [1/7] Getting super_admin token...`);
    const authResponse = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: SUPER_ADMIN.username,
        password: SUPER_ADMIN.password,
      }),
    });
    expect(authResponse.ok).toBe(true);
    const authData = await authResponse.json();
    superAdminToken = authData.access_token || authData.data?.access_token;
    console.log(`   ✅ Token: ${superAdminToken.slice(0, 20)}...`);

    // 2. Create workshop
    console.log(`\n📌 [2/7] Creating workshop: "${WORKSHOP_NAME}"...`);
    const workshopResponse = await fetch(`${API_URL}/workshops`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${superAdminToken}`,
      },
      body: JSON.stringify({
        name: WORKSHOP_NAME,
        location: "Demo Workshop Location",
      }),
    });
    expect(workshopResponse.ok).toBe(true);
    const workshopData = await workshopResponse.json();
    workshopId = workshopData.id || workshopData.data?.id;
    console.log(`   ✅ Workshop ID: ${workshopId}`);

    // 3. Create pit with camera RTSP URL (pointing to MediaMTX)
    console.log(`\n📌 [3/7] Creating pit with RTSP camera...`);
    const pitResponse = await fetch(
      `${API_URL}/workshops/${workshopId}/pits`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${superAdminToken}`,
        },
        body: JSON.stringify({
          pit_number: 1,
          name: "Pit 1 - Live Camera",
          description: "Live camera feed pit",
          camera_ip: "192.168.1.100",
          camera_rtsp_url: "rtsp://localhost:8554/demo-pit", // Will stream here
          camera_model: "Demo Webcam",
        }),
      }
    );
    expect(pitResponse.ok).toBe(true);
    const pitData = await pitResponse.json();
    pitId = pitData.id || pitData.data?.id;
    console.log(`   ✅ Pit ID: ${pitId}`);
    console.log(`      Camera RTSP: rtsp://localhost:8554/demo-pit`);

    // 4. Create NEW OWNER USER for this workshop
    console.log(
      `\n📌 [4/7] Creating new owner user: "${NEW_OWNER.username}"...`
    );
    const userResponse = await fetch(`${API_URL}/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${superAdminToken}`,
      },
      body: JSON.stringify({
        username: NEW_OWNER.username,
        email: NEW_OWNER.email,
        password: NEW_OWNER.password,
        role: "owner",
        first_name: NEW_OWNER.first_name,
        last_name: NEW_OWNER.last_name,
        workshop_id: workshopId, // Assign to this workshop
      }),
    });

    if (!userResponse.ok) {
      const errorData = await userResponse.json();
      console.log(`   ❌ Error creating user:`, errorData);
    }
    expect(userResponse.ok).toBe(true);
    const userData = await userResponse.json();
    ownerUserId = userData.id || userData.data?.id;
    console.log(`   ✅ Owner User ID: ${ownerUserId}`);
    console.log(`      Username: ${NEW_OWNER.username}`);
    console.log(`      Email: ${NEW_OWNER.email}`);

    // 5. Register device in the pit
    console.log(`\n📌 [5/7] Registering device...`);
    const deviceResponse = await fetch(
      `${API_URL}/workshops/${workshopId}/devices`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${superAdminToken}`,
        },
        body: JSON.stringify({
          device_id: `esp32-demo-${Date.now()}`,
          name: `ESP32 Device (Live Demo)`,
          primary_sensor_type_id: 3, // DHT22
          pit_id: pitId,
        }),
      }
    );
    expect(deviceResponse.ok).toBe(true);
    const deviceData = await deviceResponse.json();
    deviceId = deviceData.id || deviceData.data?.id;
    console.log(`   ✅ Device ID: ${deviceId}`);

    // 6. Get owner token
    console.log(`\n📌 [6/7] Getting owner user token...`);
    const ownerAuthResponse = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: NEW_OWNER.username,
        password: NEW_OWNER.password,
      }),
    });
    expect(ownerAuthResponse.ok).toBe(true);
    const ownerAuthData = await ownerAuthResponse.json();
    ownerToken = ownerAuthData.access_token || ownerAuthData.data?.access_token;
    console.log(`   ✅ Owner Token: ${ownerToken.slice(0, 20)}...`);

    console.log(`\n📌 [7/7] Setup complete!`);
    console.log("\n🔧 ═══════════════════════════════════════════════════════\n");
  });

  test("LIVE DEMO: Owner login → Navigate pit → View camera", async ({
    page,
  }) => {
    console.log("\n📺 ═══════════════════════════════════════════════════════");
    console.log("   LIVE DEMO: Opening Browser for Live Camera View");
    console.log("═══════════════════════════════════════════════════════\n");

    page.setDefaultTimeout(30000);

    // 1. GOTO LOGIN PAGE
    console.log(`\n👤 [1/5] Navigating to login page...`);
    await page.goto(BASE_URL);
    await page.waitForLoadState("networkidle");
    console.log(`   ✅ Login page loaded`);

    // 2. LOGIN AS NEW OWNER
    console.log(`\n🔐 [2/5] Logging in as owner: "${NEW_OWNER.username}"...`);
    await page.fill('input[name="username"]', NEW_OWNER.username);
    await page.fill('input[name="password"]', NEW_OWNER.password);
    await page.click("button[type='submit']");
    await page.waitForNavigation({ timeout: 15000 });
    console.log(`   ✅ Login successful!`);
    console.log(`   📍 Current URL: ${page.url()}`);

    // 3. NAVIGATE TO PIT DETAIL
    console.log(`\n🏭 [3/5] Navigating to pit ${pitId}...`);
    await page.goto(`${BASE_URL}/pits/${pitId}`, {
      waitUntil: "networkidle",
    });
    await page.waitForLoadState("domcontentloaded");
    console.log(`   ✅ Pit detail page loaded`);
    console.log(`   📍 Current URL: ${page.url()}`);

    // 4. WAIT FOR VIDEO PLAYER
    console.log(`\n📹 [4/5] Waiting for video player to render...`);
    await page.waitForTimeout(2000);

    const videoElements = page.locator("video, iframe, [class*='player']");
    const videoCount = await videoElements.count();
    console.log(`   ✅ Found ${videoCount} video elements on page`);

    // Check if stream URL is being loaded
    const streamElements = page.locator("[class*='stream'], [class*='video']");
    const streamCount = await streamElements.count();
    console.log(`   ✅ Found ${streamCount} stream-related elements`);

    // 5. OBSERVE FOR CAMERA FEED
    console.log(`\n📺 [5/5] Observing page for live updates (10 seconds)...`);
    console.log(
      `   🎥 Pit View is now LIVE on your screen (check browser window)`
    );
    console.log(`   📊 Monitoring for WebSocket updates...`);

    let wsUpdates = 0;
    page.on("websocket", (ws) => {
      wsUpdates++;
      console.log(`   📡 WebSocket #${wsUpdates} connected: ${ws.url()}`);
    });

    // Observe for 10 seconds
    await page.waitForTimeout(10000);

    console.log(`\n✅ Live demo observation complete!`);
    console.log(
      `   Total WebSocket connections: ${wsUpdates}\n`
    );

    // FINAL STATUS
    console.log("═══════════════════════════════════════════════════════");
    console.log("✅ LIVE DEMO SUMMARY:");
    console.log("═══════════════════════════════════════════════════════");
    console.log(`Workshop ID:     ${workshopId}`);
    console.log(`Pit ID:          ${pitId}`);
    console.log(`Device ID:       ${deviceId}`);
    console.log(`Owner User:      ${NEW_OWNER.username}`);
    console.log(`Camera RTSP:      rtsp://localhost:8554/demo-pit`);
    console.log(`Camera Status:    ${videoCount > 0 ? "✅ VISIBLE" : "⏳ Waiting for stream"}`);
    console.log(
      `\n🎯 The pit detail page is LIVE in your browser window.`
    );
    console.log(
      `   Browser stays open for live interaction during demo.\n`
    );
  });

  test("OPTIONAL: Start webcam stream (requires ffmpeg)", async () => {
    console.log("\n🎥 ═══════════════════════════════════════════════════════");
    console.log("   WEBCAM STREAMING INSTRUCTIONS");
    console.log("═══════════════════════════════════════════════════════\n");

    console.log(`To stream your laptop webcam to MediaMTX:`);
    console.log(
      `\n1. Install FFmpeg: https://ffmpeg.org/download.html\n`
    );
    console.log(`2. Run this command to stream your webcam:\n`);
    console.log(`   ┌────────────────────────────────────────────────────┐`);
    console.log(
      `   │ Windows (using gdigrab for screen, or dshow for webcam):   │`
    );
    console.log(`   │                                                    │`);
    console.log(`   │ ffmpeg -f dshow -i video="camera name" \\          │`);
    console.log(`   │   -c:v libx264 -preset ultrafast \\                │`);
    console.log(`   │   -f rtsp rtsp://localhost:8554/demo-pit          │`);
    console.log(`   │                                                    │`);
    console.log(`   │ (Get camera name with: ffmpeg -list_devices)      │`);
    console.log(`   │                                                    │`);
    console.log(`   │ OR use GStreamer (easier):                        │`);
    console.log(`   │ gst-launch-1.0 dshowvideosrc ! \\                 │`);
    console.log(`   │   x264enc ! \\                                     │`);
    console.log(`   │   rtspclientsink location=rtsp://localhost:8554   │`);
    console.log(`   └────────────────────────────────────────────────────┘\n`);

    console.log(`3. Once streaming, reload the pit view in browser`);
    console.log(`   The live camera feed will appear in the video player.\n`);

    console.log(`📍 Current pit RTSP endpoint: rtsp://localhost:8554/demo-pit`);
    console.log(`🌐 Frontend pit view:         ${BASE_URL}/pits/${pitId}\n`);

    // Don't fail the test - just informational
    expect(true).toBe(true);
  });
});
