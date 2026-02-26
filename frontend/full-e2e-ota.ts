/**
 * Full E2E: OTA Upload Page + Live Data + Camera Video
 *
 * Steps:
 *   1. Find ESP32 on network (by MAC prefix c8:f0:9e)
 *   2. Open OTA upload page at http://<esp-ip>:8080
 *   3. Login to frontend as owner
 *   4. Dashboard overview
 *   5. Devices page
 *   6. Pit Detail with live sensor data + camera video
 *   7. Jobs page
 *   8. Alerts page
 */

import { chromium, type Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE = 'http://localhost:5173';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'screenshots', 'e2e-ota');

const OWNER_USER = 'owner';
const OWNER_PASS = 'Owner@123';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function findESP32(): { ip: string; mac: string }[] {
  try {
    // Ping broadcast to populate ARP table
    execSync('ping -c 1 -t 2 192.168.29.255 2>/dev/null', { timeout: 5000 });
  } catch { /* ignore */ }

  const arpOutput = execSync('arp -a 2>/dev/null').toString();
  const devices: { ip: string; mac: string }[] = [];

  for (const line of arpOutput.split('\n')) {
    // Match Espressif MACs (c8:f0:9e prefix)
    const match = line.match(/\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+(c8:f0:9e[:\w]+)/i);
    if (match) {
      devices.push({ ip: match[1], mac: match[2] });
    }
  }
  return devices;
}

async function screenshot(page: Page, name: string) {
  const file = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`  📸 ${name}`);
  return file;
}

async function waitForPage(page: Page, timeoutMs = 3000) {
  try {
    await page.waitForLoadState('networkidle', { timeout: timeoutMs });
  } catch { /* websockets keep it active — fine */ }
  await page.waitForTimeout(1500);
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  // Clean and create screenshot dir
  if (fs.existsSync(SCREENSHOT_DIR)) fs.rmSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  console.log('\n🚀 Full E2E: OTA + Live Data + Video\n');

  // ═══════════════════════════════════════════════════════════════════════
  // 1. FIND ESP32 ON NETWORK
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 1/8: Finding ESP32 devices on network ───');
  const devices = findESP32();
  if (devices.length === 0) {
    console.error('❌ No ESP32 devices found on the network!');
    process.exit(1);
  }
  for (const d of devices) {
    console.log(`  Found: ${d.ip} (MAC: ${d.mac})`);
  }

  // Use the one we just flashed: MAC c8:f0:9e:9c:36:90
  const ourESP = devices.find(d => d.mac.includes('9c:36:90')) || devices[0];
  const espIP = ourESP.ip;
  console.log(`  ✅ Using ESP32 at ${espIP} (${ourESP.mac})\n`);

  // ═══════════════════════════════════════════════════════════════════════
  // 2. OPEN BROWSER — TEST OTA PAGE
  // ═══════════════════════════════════════════════════════════════════════
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  console.log('─── 2/8: ESP32 OTA Upload Page ───');
  await page.goto(`http://${espIP}:8080`, { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.waitForTimeout(2000);
  await screenshot(page, '01-esp32-ota-upload-page');

  // ═══════════════════════════════════════════════════════════════════════
  // 3. PUBLIC SPLASH PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 3/8: Public Splash Page (/) ───');
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page);
  await screenshot(page, '02-public-splash');

  // ═══════════════════════════════════════════════════════════════════════
  // 4. LOGIN AS OWNER
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 4/8: Login ───');
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page);
  await page.fill('input[name="username"], input[type="text"]', OWNER_USER);
  await page.waitForTimeout(300);
  await page.fill('input[name="password"], input[type="password"]', OWNER_PASS);
  await page.waitForTimeout(300);
  await screenshot(page, '03-login-filled');

  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
  await waitForPage(page, 5000);
  await screenshot(page, '04-login-success-dashboard');

  // ═══════════════════════════════════════════════════════════════════════
  // 5. DASHBOARD
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 5/8: Dashboard ───');
  await page.goto(`${BASE}/admin/dashboard`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '05-dashboard-overview');

  // ═══════════════════════════════════════════════════════════════════════
  // 6. DEVICES PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 6/8: Devices Page ───');
  await page.goto(`${BASE}/admin/devices`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '06-devices-list');

  // ═══════════════════════════════════════════════════════════════════════
  // 7. PIT DETAIL — LIVE SENSOR DATA + CAMERA VIDEO
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 7/8: Pit Detail — Live Data + Camera ───');
  await page.goto(`${BASE}/admin/pits/10`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '07-pit-detail-initial');

  // Wait for video stream to load (HLS takes a few seconds)
  console.log('  Waiting for video stream (10s)...');
  await page.waitForTimeout(10000);
  await screenshot(page, '08-pit-detail-video-loaded');

  // Scroll to see sensor readings
  await page.evaluate(() => window.scrollBy(0, 500));
  await page.waitForTimeout(3000);
  await screenshot(page, '09-pit-detail-sensors');

  // Scroll back up to see video + data together
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(2000);
  await screenshot(page, '10-pit-detail-full-view');

  // ═══════════════════════════════════════════════════════════════════════
  // 8. JOBS + ALERTS
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 8/8: Jobs & Alerts ───');
  await page.goto(`${BASE}/admin/jobs`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '12-jobs-list');

  await page.goto(`${BASE}/admin/alerts`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 3000);
  await screenshot(page, '13-alerts-list');

  // ═══════════════════════════════════════════════════════════════════════
  // DONE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('\n✅ E2E Complete! Screenshots saved to screenshots/e2e-ota/');
  console.log('📂 ' + SCREENSHOT_DIR);
  console.log('\n⏸️  Browser stays open for inspection. Press Ctrl+C to close.\n');

  await page.waitForTimeout(120000);
  await browser.close();
}

main().catch((err) => {
  console.error('E2E failed:', err);
  process.exit(1);
});
