import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';
const API = 'http://localhost:8000/api/v1';
const SCREENSHOTS = '../screenshots/demo';

test.describe('PPF Live Demo — Full Walkthrough', () => {
  test('Complete demo: Login → Workshop → Owner → Pit → Device → Live', async ({ page }) => {
    test.setTimeout(300_000); // 5 minutes

    // ═══════════════════════════════════════════════════════════════════
    // STEP 1: LOGIN AS SUPER ADMIN
    // ═══════════════════════════════════════════════════════════════════
    await page.goto(`${BASE}/login`);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: `${SCREENSHOTS}/01-login--empty.png`, fullPage: true });

    await page.fill('#username', 'super_admin');
    await page.fill('#password', 'SuperAdmin@123');
    await page.screenshot({ path: `${SCREENSHOTS}/02-login--filled.png`, fullPage: true });

    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${SCREENSHOTS}/03-dashboard--empty.png`, fullPage: true });

    // ═══════════════════════════════════════════════════════════════════
    // STEP 2: CREATE WORKSHOP (Admin Panel)
    // ═══════════════════════════════════════════════════════════════════
    await page.goto(`${BASE}/admin`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${SCREENSHOTS}/04-admin--empty.png`, fullPage: true });

    await page.fill('input[placeholder="e.g. Delhi PPF Hub"]', 'Demo Workshop');
    await page.fill('input[placeholder="e.g. delhi-ppf"]', 'demo-workshop');
    const adminForm = page.locator('form').first();
    await adminForm.locator('input[type="email"]').fill('demo@ppf.com');
    await adminForm.locator('.grid.grid-cols-2 input[type="text"]').fill('+91-9876543210');
    await page.screenshot({ path: `${SCREENSHOTS}/05-admin--workshop-filled.png`, fullPage: true });

    await page.click('button:has-text("Create Workshop")');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS}/06-admin--workshop-created.png`, fullPage: true });

    // ═══════════════════════════════════════════════════════════════════
    // STEP 3: CREATE PIT (Admin Panel — scroll down)
    // ═══════════════════════════════════════════════════════════════════
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    await page.locator('select').selectOption({ index: 1 });
    await page.locator('input[type="number"][min="1"]').fill('1');
    await page.fill('input[placeholder="e.g. Bay 1 - Main Pit"]', 'Demo Pit Alpha');
    await page.fill('input[placeholder="e.g. PPF application bay with camera"]', 'Live demo pit with ESP32 + camera');
    await page.fill('input[placeholder="e.g. 192.168.29.64"]', '192.168.29.64');
    await page.fill('input[placeholder="rtsp://..."]', 'rtsp://admin:Hik@12345@192.168.29.64/Streaming/Channels/101');
    await page.screenshot({ path: `${SCREENSHOTS}/07-admin--pit-filled.png`, fullPage: true });

    await page.click('button:has-text("Create Pit")');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS}/08-admin--pit-created.png`, fullPage: true });

    // ═══════════════════════════════════════════════════════════════════
    // STEP 4: CREATE OWNER USER VIA API (super_admin creates owner)
    //         Then we log in as the owner for the rest of the demo
    // ═══════════════════════════════════════════════════════════════════
    // Get super_admin token
    const loginResp = await (await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'super_admin', password: 'SuperAdmin@123' }),
    })).json();
    const token = loginResp.data.access_token;

    // Create owner user for workshop 1
    const ownerResp = await (await fetch(`${API}/workshops/1/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        username: 'demo_owner',
        password: 'DemoOwner@123',
        role: 'owner',
        first_name: 'Meharban',
        last_name: 'Singh',
      }),
    })).json();
    console.log('Owner created:', JSON.stringify(ownerResp));

    // ═══════════════════════════════════════════════════════════════════
    // STEP 5: LOGOUT AND LOGIN AS OWNER
    // ═══════════════════════════════════════════════════════════════════
    // Click logout
    await page.click('button:has-text("Log out")');
    await page.waitForURL('**/login', { timeout: 5000 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOTS}/09-login--after-logout.png`, fullPage: true });

    // Login as owner
    await page.fill('#username', 'demo_owner');
    await page.fill('#password', 'DemoOwner@123');
    await page.screenshot({ path: `${SCREENSHOTS}/10-login--owner-filled.png`, fullPage: true });

    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Handle change password page if redirected
    if (page.url().includes('change-password')) {
      await page.screenshot({ path: `${SCREENSHOTS}/11-change-password.png`, fullPage: true });
      await page.getByLabel('Current Password').fill('DemoOwner@123');
      await page.getByLabel('New Password', { exact: false }).first().fill('DemoOwner@456');
      await page.getByLabel('Confirm', { exact: false }).fill('DemoOwner@456');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: `${SCREENSHOTS}/12-password-changed.png`, fullPage: true });

      // May need to re-login with new password
      if (page.url().includes('login')) {
        await page.fill('#username', 'demo_owner');
        await page.fill('#password', 'DemoOwner@456');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(2000);
      }
    }

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${SCREENSHOTS}/13-dashboard--owner-view.png`, fullPage: true });

    // ═══════════════════════════════════════════════════════════════════
    // STEP 6: ADD STAFF MEMBER
    // ═══════════════════════════════════════════════════════════════════
    await page.goto(`${BASE}/staff`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${SCREENSHOTS}/14-staff--empty.png`, fullPage: true });

    await page.click('button:has-text("Add Staff")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOTS}/15-staff--modal-open.png`, fullPage: true });

    await page.getByLabel('Username *').fill('raj_kumar');
    await page.getByLabel('Password *').fill('RajKumar@123');
    await page.getByLabel('First Name').fill('Raj');
    await page.getByLabel('Last Name').fill('Kumar');
    await page.screenshot({ path: `${SCREENSHOTS}/16-staff--form-filled.png`, fullPage: true });

    await page.getByRole('button', { name: 'Create' }).click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${SCREENSHOTS}/17-staff--created.png`, fullPage: true });

    // Close modal if visible
    for (const text of ['Done', 'Close', 'Got it']) {
      const btn = page.getByRole('button', { name: text });
      if (await btn.isVisible({ timeout: 500 }).catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(300);
        break;
      }
    }

    // ═══════════════════════════════════════════════════════════════════
    // STEP 7: REGISTER ESP32 DEVICE
    // ═══════════════════════════════════════════════════════════════════
    await page.goto(`${BASE}/devices`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: `${SCREENSHOTS}/18-devices--empty.png`, fullPage: true });

    await page.click('button:has-text("Register")');
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOTS}/19-devices--register-modal.png`, fullPage: true });

    // Fill device ID
    await page.locator('#device-id').fill('ESP32-083AF2A9F084');
    await page.waitForTimeout(300);

    // Select pit
    const pitSelect = page.locator('select').first();
    if (await pitSelect.isVisible({ timeout: 1000 }).catch(() => false)) {
      await pitSelect.selectOption({ index: 1 });
    }
    await page.waitForTimeout(300);

    // MAC address
    const macInput = page.locator('input[placeholder*="AA:BB"]').first();
    if (await macInput.isVisible({ timeout: 500 }).catch(() => false)) {
      await macInput.fill('C8:F0:9E:A6:2A:84');
    }
    await page.screenshot({ path: `${SCREENSHOTS}/20-devices--register-filled.png`, fullPage: true });

    // Submit
    await page.getByRole('button', { name: 'Register' }).last().click();
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${SCREENSHOTS}/21-devices--registered.png`, fullPage: true });

    // Close modal
    for (const text of ['Done', 'Close', 'Got it']) {
      const btn = page.getByRole('button', { name: text });
      if (await btn.isVisible({ timeout: 500 }).catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(300);
        break;
      }
    }

    // ═══════════════════════════════════════════════════════════════════
    // STEP 8: DASHBOARD — LIVE PIT WITH SENSOR DATA
    // ═══════════════════════════════════════════════════════════════════
    await page.goto(`${BASE}/dashboard`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // Wait for live data
    await page.screenshot({ path: `${SCREENSHOTS}/22-dashboard--live-pit.png`, fullPage: true });

    // ═══════════════════════════════════════════════════════════════════
    // STEP 9: PIT DETAIL — LIVE SENSORS + CAMERA FEED
    // ═══════════════════════════════════════════════════════════════════
    const pitLink = page.locator('a[href*="/pits/"]').first();
    if (await pitLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await pitLink.click();
    } else {
      await page.goto(`${BASE}/pits/1`);
    }
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);
    await page.screenshot({ path: `${SCREENSHOTS}/23-pit-detail--live.png`, fullPage: true });

    // Wait for sensor updates
    await page.waitForTimeout(12000);
    await page.screenshot({ path: `${SCREENSHOTS}/24-pit-detail--updated.png`, fullPage: true });

    // Final view
    await page.waitForTimeout(10000);
    await page.screenshot({ path: `${SCREENSHOTS}/25-pit-detail--final.png`, fullPage: true });

    console.log('\n========================================');
    console.log('  DEMO COMPLETE — 25 screenshots saved');
    console.log('  Check: screenshots/demo/');
    console.log('========================================\n');
  });
});
