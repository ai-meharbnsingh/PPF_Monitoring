/**
 * Watch Live Pit — Login and pause for observation
 * Pit 30: Hikvision camera (192.168.29.64) → MediaMTX → WebRTC
 * Pit 27: Live ESP32 sensor data (28.3°C / 65.9%)
 */

import { test } from '@playwright/test';

test.setTimeout(0); // No timeout — user controls when to close

const BASE_URL   = 'http://localhost:5173';
const LIVE_PIT   = 30;   // Wave 3 pit — Hikvision camera configured
const SENSOR_PIT = 27;   // Previous pit — live ESP32 sensor data

test('Live Pit — Login and observe', async ({ page }) => {

  // ── Login ────────────────────────────────────────────────────────────────
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');
  await page.fill('input[placeholder="Enter your username"]', 'super_admin');
  await page.fill('input[placeholder="Enter your password"]', '4grZStIoPAX11CEEymamBw');
  await page.click('button:has-text("Sign In")');
  await page.waitForURL(/.*\/dashboard/, { timeout: 15000 });

  // ── Navigate to live pit ─────────────────────────────────────────────────
  await page.goto(`${BASE_URL}/pits/${LIVE_PIT}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000); // let video player initialise

  // ── STOP HERE — user observes ─────────────────────────────────────────────
  await page.pause();
});
