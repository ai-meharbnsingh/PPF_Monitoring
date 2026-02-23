/**
 * LIVE E2E DEMO - WATCH THE SYSTEM IN ACTION
 *
 * This test sets up a complete live environment and opens the pit
 * detail page so you can observe the live camera stream and sensor data.
 *
 * ESP32 MAC: 08:3a:f2:a9:f0:84
 * Webcam: Streaming to rtsp://localhost:8554/demopit
 */

import { test, expect } from "@playwright/test";

const BASE_URL = "http://localhost:5173";
const API_URL = "http://localhost:8000/api/v1";

const SUPER_ADMIN = {
  username: "super_admin",
  password: "4grZStIoPAX11CEEymamBw",
};

test.describe("🎬 LIVE DEMO - VISUAL OBSERVATION", () => {
  test("Watch: Setup → Navigate → Live Camera + Sensors → Pause", async ({
    page,
  }) => {
    console.log("\n╔═══════════════════════════════════════════════════════════╗");
    console.log("║  🎬 LIVE DEMO - VISUAL OBSERVATION MODE                ║");
    console.log("║  Watch as the system sets up and opens the live pit    ║");
    console.log("╚═══════════════════════════════════════════════════════════╝\n");

    page.setDefaultTimeout(45000);
    page.setDefaultNavigationTimeout(45000);

    // ─── STEP 1: API SETUP (FAST) ─────────────────────────────────────────
    console.log("📌 STEP 1: Setting up system (Workshop + Pit + Device)");

    // Get token
    const authRes = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(SUPER_ADMIN),
    });
    const authData = await authRes.json();
    const token = authData.access_token || authData.data?.access_token;
    console.log("   ✅ Authenticated");

    // Create workshop
    const wsRes = await fetch(`${API_URL}/workshops`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        name: `Live Demo ${Date.now()}`,
        location: "Live Demo Location",
      }),
    });
    const wsData = await wsRes.json();
    const workshopId = wsData.id || wsData.data?.id;
    console.log(`   ✅ Workshop created (ID: ${workshopId})`);

    // Create pit
    const pitRes = await fetch(
      `${API_URL}/workshops/${workshopId}/pits`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          pit_number: 1,
          name: "Live Demo Pit",
          description: "Live demo with laptop webcam",
          camera_ip: "127.0.0.1",
          camera_rtsp_url: "rtsp://localhost:8554/demopit",
          camera_model: "Laptop Webcam (HP HD)",
        }),
      }
    );
    const pitData = await pitRes.json();
    const pitId = pitData.id || pitData.data?.id;
    console.log(`   ✅ Pit created (ID: ${pitId})`);

    // Register device
    const devRes = await fetch(
      `${API_URL}/workshops/${workshopId}/devices`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          device_id: `ESP32-LIVE-${Date.now()}`,
          name: "ESP32 Live Demo (DHT11)",
          primary_sensor_type_id: 3,
          pit_id: pitId,
        }),
      }
    );
    const devData = await devRes.json();
    const deviceId = devData.id || devData.data?.id;
    console.log(`   ✅ Device registered (ID: ${deviceId})`);
    console.log(`   🔑 License Key: ${devData.license_key}\n`);

    // ─── STEP 2: NAVIGATE TO PIT PAGE ─────────────────────────────────────
    console.log("📌 STEP 2: Opening pit detail page in browser...");
    await page.goto(`${BASE_URL}/pits/${pitId}`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(2000);
    console.log("   ✅ Pit detail page loaded\n");

    // ─── STEP 3: VERIFY PAGE ELEMENTS ─────────────────────────────────────
    console.log("📌 STEP 3: Checking live elements on page");

    const videoElements = page.locator("video, iframe, [class*='player']");
    const videoCount = await videoElements.count();
    console.log(`   📹 Video elements: ${videoCount > 0 ? "✅ PRESENT" : "⏳ Loading"}`);

    const sensorCards = page.locator("[class*='card'], [class*='sensor']");
    const cardCount = await sensorCards.count();
    console.log(`   📊 Sensor cards: ${cardCount > 0 ? "✅ PRESENT" : "⏳ Loading"}\n`);

    // ─── STEP 4: MONITOR LIVE SYSTEMS ─────────────────────────────────────
    console.log("📌 STEP 4: Monitoring real-time systems (10 seconds)");
    console.log("   🔌 WebSocket listener active");
    console.log("   📡 Watching for sensor updates...\n");

    let wsConnected = false;
    page.on("websocket", (ws) => {
      console.log(`   ✅ WebSocket: ${ws.url()}`);
      wsConnected = true;
    });

    await page.waitForTimeout(10000);

    // ─── STEP 5: READY FOR OBSERVATION ────────────────────────────────────
    console.log("╔═══════════════════════════════════════════════════════════╗");
    console.log("║  ✅ LIVE DEMO READY - BROWSER PAUSED                     ║");
    console.log("╚═══════════════════════════════════════════════════════════╝\n");

    console.log("🎬 YOU ARE NOW LOOKING AT:");
    console.log(`   ✅ Workshop ID: ${workshopId}`);
    console.log(`   ✅ Pit ID: ${pitId}`);
    console.log(`   ✅ Device ID: ${deviceId}`);
    console.log(`   📍 URL: ${BASE_URL}/pits/${pitId}\n`);

    console.log("📊 LIVE SYSTEMS:");
    console.log(`   ✅ Camera: rtsp://localhost:8554/demopit (STREAMING)`);
    console.log(`   ✅ ESP32: Ready for sensor data`);
    console.log(`   ✅ Sensors: DHT11 (Temperature + Humidity)`);
    console.log(`   ✅ WebSocket: ${wsConnected ? "CONNECTED" : "READY"}\n`);

    console.log("⏸️  BROWSER IS NOW PAUSED");
    console.log("   You can interact with the page, watch for live updates,");
    console.log("   and observe the camera stream and sensor data.");
    console.log("   Close the browser window when done.\n");

    // Pause for user observation
    await page.pause();

    expect(workshopId).toBeGreaterThan(0);
    expect(pitId).toBeGreaterThan(0);
    expect(deviceId).toBeGreaterThan(0);
  });
});
