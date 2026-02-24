/**
 * Hikvision Camera — Web Activation + IP Configuration
 *
 * 1. Opens http://192.168.1.64
 * 2. Detects if activation needed or login page
 * 3. Activates / logs in
 * 4. Changes camera IP to 192.168.29.64 (static) on main network
 * 5. Verifies camera is accessible on new IP
 */
const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const CAMERA_DEFAULT_IP = '192.168.1.64';
const CAMERA_NEW_IP     = '192.168.29.64';
const GATEWAY           = '192.168.29.1';
const DNS               = '8.8.8.8';
const ADMIN_PASS        = 'Hik@12345';   // New password to set (8+ chars, mixed)
const SS_DIR            = path.join(__dirname, 'screenshots');
fs.mkdirSync(SS_DIR, { recursive: true });

let n = 0;
const ss = async (page, name) => {
  const f = path.join(SS_DIR, `hik-${String(n++).padStart(2,'0')}--${name}.png`);
  await page.screenshot({ path: f, fullPage: true });
  console.log(`  📸 ${f}`);
};

(async () => {
  console.log('\n╔══════════════════════════════════════════════════╗');
  console.log('║  Hikvision Camera Activation + Network Setup    ║');
  console.log('╚══════════════════════════════════════════════════╝\n');

  const browser = await chromium.launch({ headless: false, slowMo: 600 });
  const ctx  = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  // ── 1. OPEN CAMERA ─────────────────────────────────────────────────────
  console.log(`[1] Opening http://${CAMERA_DEFAULT_IP} ...`);
  await page.goto(`http://${CAMERA_DEFAULT_IP}`, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(3000);
  await ss(page, '01-initial-load');

  const title = await page.title();
  console.log(`    Title: "${title}"`);

  // ── 2. DETECT STATE ─────────────────────────────────────────────────────
  const html = await page.content();
  const isActivation = html.includes('activation') || html.includes('Activation') ||
                       html.includes('createPassword') || html.includes('init') ||
                       html.includes('Initialize');
  const isLogin      = html.includes('login') || html.includes('Login') ||
                       await page.$('input[type="password"]').then(e => !!e);

  console.log(`    Detected: activation=${isActivation} login=${isLogin}`);

  // ── 3. ACTIVATION (first boot) ──────────────────────────────────────────
  if (isActivation) {
    console.log('\n[3] Activation page — setting new admin password...');

    // Look for password fields
    const pwFields = await page.$$('input[type="password"]');
    console.log(`    Password fields found: ${pwFields.length}`);

    for (const f of pwFields) {
      await f.fill(ADMIN_PASS);
      await page.waitForTimeout(300);
    }
    await ss(page, '02-activation-filled');

    // Click OK/Activate button
    for (const sel of ['button:has-text("OK")', 'button:has-text("Activate")',
                        'input[type="submit"]', '.btn-primary', '#btn-ok']) {
      const btn = await page.$(sel);
      if (btn && await btn.isVisible()) { await btn.click(); break; }
    }
    await page.waitForTimeout(3000);
    await ss(page, '03-after-activation');
    console.log('    Activation submitted.');

    // Reload to login page
    await page.goto(`http://${CAMERA_DEFAULT_IP}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
    await page.waitForTimeout(2000);
  }

  // ── 4. LOGIN ────────────────────────────────────────────────────────────
  console.log('\n[4] Logging in as admin...');
  await ss(page, '04-login-page');

  // Try filling login form
  const userField = await page.$('input[type="text"]:not([disabled]), input[name*="user"], input[name*="name"], #username');
  if (userField) { await userField.fill('admin'); }

  const pwField = await page.$('input[type="password"]');
  if (pwField) {
    await pwField.fill(ADMIN_PASS);
  } else {
    console.log('    No password field found — may already be logged in or different UI');
  }
  await page.waitForTimeout(500);
  await ss(page, '05-login-filled');

  // Submit
  for (const sel of ['button[type="submit"]', 'input[type="submit"]',
                      'button:has-text("Login")', 'button:has-text("Sign In")',
                      '.login-btn', '#loginBtn']) {
    const btn = await page.$(sel);
    if (btn && await btn.isVisible()) {
      await btn.click();
      console.log(`    Clicked: ${sel}`);
      break;
    }
  }
  await page.waitForTimeout(4000);
  await ss(page, '06-after-login');

  const afterLoginTitle = await page.title();
  const afterLoginURL   = page.url();
  console.log(`    Post-login title: "${afterLoginTitle}"`);
  console.log(`    Post-login URL: ${afterLoginURL}`);

  // ── 5. NAVIGATE TO NETWORK SETTINGS ─────────────────────────────────────
  console.log('\n[5] Navigating to Network → TCP/IP settings...');

  // Hikvision web UI uses JavaScript-rendered menus
  // Try common navigation patterns
  const navSelectors = [
    'text=Configuration',
    'text=Network',
    'a[href*="network"]',
    '[title*="network"]',
    '.nav-item:has-text("Configuration")',
  ];

  let navFound = false;
  for (const sel of navSelectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) {
        await el.click();
        console.log(`    Clicked nav: ${sel}`);
        await page.waitForTimeout(2000);
        navFound = true;
        await ss(page, '07-after-nav-click');
        break;
      }
    } catch {}
  }

  if (!navFound) {
    console.log('    Standard nav not found — trying direct URL for TCP/IP config');
    // Hikvision direct config URL
    for (const url of [
      `http://${CAMERA_DEFAULT_IP}/doc/page/config.asp`,
      `http://${CAMERA_DEFAULT_IP}/ISAPI/System/Network/interfaces/1`,
    ]) {
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 8000 });
        await page.waitForTimeout(2000);
        await ss(page, '07-direct-config-url');
        break;
      } catch {}
    }
  }

  // Dump current page to understand the UI structure
  const bodyText = (await page.innerText('body').catch(() => '')).substring(0, 600);
  console.log(`    Page content preview: ${bodyText}`);

  // Get all links on page for navigation clues
  const links = await page.$$eval('a', els => els.slice(0,20).map(e => ({
    text: e.innerText.trim(), href: e.href
  })).filter(x => x.text.length > 0));
  console.log('    Available links:', JSON.stringify(links.slice(0, 10), null, 2));

  await ss(page, '08-network-page');

  // ── 6. SET STATIC IP ────────────────────────────────────────────────────
  console.log(`\n[6] Attempting to set static IP to ${CAMERA_NEW_IP}...`);

  // Look for IP address input fields
  const ipInputs = await page.$$('input[type="text"]');
  console.log(`    Text inputs on page: ${ipInputs.length}`);

  // Try ISAPI direct call to change IP (Hikvision REST API)
  console.log('\n[6b] Trying ISAPI REST call to set IP directly...');
  try {
    const resp = await page.evaluate(async (args) => {
      const { ip, gw, dns } = args;
      const xmlBody = `<?xml version="1.0" encoding="UTF-8"?>
<NetworkInterface>
  <id>1</id>
  <IPAddress>
    <ipVersion>dual</ipVersion>
    <addressingType>static</addressingType>
    <ipAddress>${ip}</ipAddress>
    <subnetMask>255.255.255.0</subnetMask>
    <DefaultGateway>
      <ipAddress>${gw}</ipAddress>
    </DefaultGateway>
    <PrimaryDNS>
      <ipAddress>${dns}</ipAddress>
    </PrimaryDNS>
  </IPAddress>
</NetworkInterface>`;
      const r = await fetch('/ISAPI/System/Network/interfaces/1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/xml' },
        body: xmlBody,
      });
      return { status: r.status, text: await r.text() };
    }, { ip: CAMERA_NEW_IP, gw: GATEWAY, dns: DNS });

    console.log(`    ISAPI response: ${resp.status} — ${resp.text.substring(0, 200)}`);
    await ss(page, '09-isapi-ip-change');

    if (resp.status === 200) {
      console.log(`\n  ✅ IP CHANGED TO ${CAMERA_NEW_IP} via ISAPI!`);
      console.log('    Camera will reboot... waiting 15s');
      await page.waitForTimeout(15000);
    }
  } catch (e) {
    console.log(`    ISAPI call error: ${e.message}`);
  }

  await ss(page, '10-final-state');

  // ── 7. VERIFY NEW IP ────────────────────────────────────────────────────
  console.log(`\n[7] Verifying camera on new IP ${CAMERA_NEW_IP}...`);
  try {
    await page.goto(`http://${CAMERA_NEW_IP}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(3000);
    await ss(page, '11-new-ip-verified');
    console.log(`  ✅ Camera reachable at http://${CAMERA_NEW_IP}`);
  } catch {
    console.log(`  ⚠️  Camera not yet at ${CAMERA_NEW_IP} — may need 192.168.29.x subnet`);
    console.log('     Camera is still accessible at 192.168.1.64');
  }

  console.log('\n╔══════════════════════════════════════════════════╗');
  console.log(`║  Password : admin / ${ADMIN_PASS}              ║`);
  console.log(`║  New IP   : ${CAMERA_NEW_IP}                  ║`);
  console.log('╚══════════════════════════════════════════════════╝\n');

  await page.waitForTimeout(3000);
  await browser.close();
})();
