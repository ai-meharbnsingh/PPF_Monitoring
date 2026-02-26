/**
 * Full E2E Walkthrough — Playwright (headed, slowMo:500)
 *
 * Walks through every page of the integrated Rishabh UI:
 *   1. Public Splash (/)
 *   2. Login Page (/login)
 *   3. Login as owner → Dashboard
 *   4. Dashboard (/admin/dashboard)
 *   5. Jobs Page (/admin/jobs)
 *   6. Job Detail (BMW M4 job)
 *   7. Alerts Page (/admin/alerts)
 *   8. Devices Page (/admin/devices)
 *   9. Staff Page (/admin/staff)
 *  10. Admin/Metrics Page (/admin/metrics)
 *  11. Customer Tracking Page (/track/:token)
 *  12. Pit Detail with camera (/admin/pits/10) — FINAL
 */

import { chromium, type Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE = 'http://localhost:5173';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'screenshots', 'walkthrough');
const CUSTOMER_TOKEN = 'hE_Lptgp7J04qsgvf9v_ZmHXFZUCJC0p1DhbcVKOBbE';

// Owner credentials
const OWNER_USER = 'owner';
const OWNER_PASS = 'Owner@123';

async function screenshot(page: Page, name: string) {
  const ts = Date.now();
  const file = path.join(SCREENSHOT_DIR, `${name}--${ts}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`  📸 ${name}`);
  return file;
}

async function waitForPage(page: Page, timeoutMs = 3000) {
  try {
    await page.waitForLoadState('networkidle', { timeout: timeoutMs });
  } catch {
    // networkidle may not fire if websockets are active — that's fine
  }
  await page.waitForTimeout(1500);
}

async function main() {
  // Clean and create screenshot dir
  if (fs.existsSync(SCREENSHOT_DIR)) fs.rmSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  console.log('\n🚀 Starting Playwright Walkthrough (headed, slowMo:500)\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  // ═══════════════════════════════════════════════════════════════════════
  // 1. PUBLIC SPLASH PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 1/12: Public Splash Page (/) ───');
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page);
  await screenshot(page, '01-public-splash');

  // ═══════════════════════════════════════════════════════════════════════
  // 2. LOGIN PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 2/12: Login Page (/login) ───');
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page);
  await screenshot(page, '02-login--empty');

  // ═══════════════════════════════════════════════════════════════════════
  // 3. LOGIN AS OWNER
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 3/12: Logging in as owner ───');
  await page.fill('input[name="username"], input[type="text"]', OWNER_USER);
  await page.waitForTimeout(300);
  await page.fill('input[name="password"], input[type="password"]', OWNER_PASS);
  await page.waitForTimeout(300);
  await screenshot(page, '03-login--filled');

  // Click login button
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
  await waitForPage(page, 5000);
  await screenshot(page, '04-login--after-submit');

  // ═══════════════════════════════════════════════════════════════════════
  // 4. DASHBOARD
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 4/12: Dashboard (/admin/dashboard) ───');
  await page.goto(`${BASE}/admin/dashboard`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '05-dashboard--overview');

  // ═══════════════════════════════════════════════════════════════════════
  // 5. JOBS PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 5/12: Jobs Page (/admin/jobs) ───');
  await page.goto(`${BASE}/admin/jobs`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '06-jobs--list');

  // ═══════════════════════════════════════════════════════════════════════
  // 6. JOB DETAIL (BMW M4)
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 6/12: Job Detail — BMW M4 ───');
  // Try clicking on the job card, or navigate directly
  try {
    const jobLink = page.locator('a[href*="/admin/jobs/"]').first();
    if (await jobLink.isVisible({ timeout: 2000 })) {
      await jobLink.click();
      await waitForPage(page, 5000);
    } else {
      await page.goto(`${BASE}/admin/jobs/4`, { waitUntil: 'domcontentloaded' });
      await waitForPage(page, 5000);
    }
  } catch {
    await page.goto(`${BASE}/admin/jobs/4`, { waitUntil: 'domcontentloaded' });
    await waitForPage(page, 5000);
  }
  await screenshot(page, '07-job-detail--bmw-m4');

  // ═══════════════════════════════════════════════════════════════════════
  // 7. ALERTS PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 7/12: Alerts Page (/admin/alerts) ───');
  await page.goto(`${BASE}/admin/alerts`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page);
  await screenshot(page, '08-alerts--list');

  // ═══════════════════════════════════════════════════════════════════════
  // 8. DEVICES PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 8/12: Devices Page (/admin/devices) ───');
  await page.goto(`${BASE}/admin/devices`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '09-devices--list');

  // ═══════════════════════════════════════════════════════════════════════
  // 9. STAFF PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 9/12: Staff Page (/admin/staff) ───');
  await page.goto(`${BASE}/admin/staff`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '10-staff--list');

  // ═══════════════════════════════════════════════════════════════════════
  // 10. ADMIN METRICS PAGE
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 10/12: Admin Metrics (/admin/metrics) ───');
  await page.goto(`${BASE}/admin/metrics`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '11-admin-metrics');

  // ═══════════════════════════════════════════════════════════════════════
  // 11. CUSTOMER TRACKING PAGE (public, no auth)
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 11/12: Customer Tracking Page ───');
  await page.goto(`${BASE}/track/${CUSTOMER_TOKEN}`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 5000);
  await screenshot(page, '12-tracking--customer-view');

  // ═══════════════════════════════════════════════════════════════════════
  // 12. PIT DETAIL WITH CAMERA (FINAL — end here)
  // ═══════════════════════════════════════════════════════════════════════
  console.log('─── 12/12: Pit Detail + Camera (/admin/pits/10) ───');
  await page.goto(`${BASE}/admin/pits/10`, { waitUntil: 'domcontentloaded' });
  await waitForPage(page, 8000);
  await screenshot(page, '13-pit-detail--camera-view');

  // Scroll down to see full pit detail with sensors
  await page.evaluate(() => window.scrollBy(0, 600));
  await page.waitForTimeout(2000);
  await screenshot(page, '14-pit-detail--sensors-scrolled');

  console.log('\n✅ Walkthrough complete! Screenshots saved to screenshots/walkthrough/');
  console.log('📂 ' + SCREENSHOT_DIR);
  console.log('\n⏸️  Browser stays open for manual inspection. Press Ctrl+C to close.\n');

  // Keep browser open so user can inspect
  await page.waitForTimeout(120000);
  await browser.close();
}

main().catch((err) => {
  console.error('Walkthrough failed:', err);
  process.exit(1);
});
