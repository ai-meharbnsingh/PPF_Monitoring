/**
 * Demo: Create a new user from Super Admin panel
 * Logs in as super_admin → navigates to Staff page → creates new user → pauses
 */

import { test } from '@playwright/test';

test.setTimeout(0);

const BASE_URL = 'http://localhost:5173';

test('Create new user via Super Admin', async ({ page }) => {

  // ── Login as super_admin ─────────────────────────────────────────────────
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);

  await page.fill('input[placeholder="Enter your username"]', 'super_admin');
  await page.fill('input[placeholder="Enter your password"]', 'SuperAdmin@123');
  await page.click('button:has-text("Sign In")');
  await page.waitForURL(/.*\/dashboard/, { timeout: 15000 });
  await page.waitForTimeout(1000);

  // ── Go to Staff page ─────────────────────────────────────────────────────
  await page.click('text=Staff');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // ── PAUSE — you are now on the Staff / Create User page ─────────────────
  await page.pause();
});
