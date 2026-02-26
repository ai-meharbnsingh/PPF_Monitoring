/**
 * Quick camera test — login, go to pit detail, verify video loads
 */
import { chromium } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const BASE = 'http://localhost:5173';
const SCREENSHOT_DIR = path.resolve(__dirname, '..', 'screenshots', 'camera-test');

async function main() {
  if (fs.existsSync(SCREENSHOT_DIR)) fs.rmSync(SCREENSHOT_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // Login
  console.log('Logging in...');
  await page.goto(`${BASE}/login`);
  await page.waitForTimeout(1500);
  await page.fill('input[name="username"], input[type="text"]', 'owner');
  await page.fill('input[name="password"], input[type="password"]', 'Owner@123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(4000);

  // Go to pit detail
  console.log('Navigating to Pit Detail...');
  await page.goto(`${BASE}/admin/pits/10`);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01-pit-detail-initial.png'), fullPage: true });
  console.log('  Screenshot: 01-pit-detail-initial');

  // Wait for video to load (HLS takes a few seconds)
  console.log('Waiting for video stream to load (10s)...');
  await page.waitForTimeout(10000);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02-pit-detail-video-loaded.png'), fullPage: true });
  console.log('  Screenshot: 02-pit-detail-video-loaded');

  // Scroll to see sensors
  await page.evaluate(() => window.scrollBy(0, 500));
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03-pit-detail-scrolled.png'), fullPage: true });
  console.log('  Screenshot: 03-pit-detail-scrolled');

  console.log('\nDone! Browser stays open for inspection. Press Ctrl+C to close.');
  await page.waitForTimeout(120000);
  await browser.close();
}

main().catch(console.error);
