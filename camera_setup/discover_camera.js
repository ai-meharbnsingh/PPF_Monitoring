const { chromium } = require('playwright');
const path = require('path');

const SS_DIR = path.join(__dirname, 'screenshots');

// All common Hikvision + OEM default credentials to try
const CREDS = [
  { user: 'admin', pass: '12345' },
  { user: 'admin', pass: '123456' },
  { user: 'admin', pass: 'admin' },
  { user: 'admin', pass: '' },
  { user: 'admin', pass: 'admin123' },
  { user: 'admin', pass: 'Admin123' },
  { user: 'admin', pass: '1234' },
  { user: 'admin', pass: 'hik12345' },
];

let ssCount = 0;
async function ss(page, name) {
  const file = path.join(SS_DIR, `disc-${String(ssCount++).padStart(2,'0')}--${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`  [SCREENSHOT] ${file}`);
  return file;
}

async function tryLogin(page, user, pass) {
  // Clear and fill username
  const userField = await page.$('#loginUsername-inputEl');
  if (userField) {
    await userField.click({ clickCount: 3 });
    await userField.fill(user);
  }
  // Clear and fill password
  const pwField = await page.$('#loginPassword-inputEl');
  if (pwField) {
    await pwField.click({ clickCount: 3 });
    await pwField.fill(pass);
  }
  await page.waitForTimeout(400);

  // Click Login button (it's an <a> tag)
  const loginBtn = await page.$('.login_button');
  if (loginBtn) {
    await loginBtn.click();
  } else {
    await page.keyboard.press('Enter');
  }

  await page.waitForTimeout(2500);

  // Check if still on login page
  const stillLogin = await page.$('#loginPassword-inputEl');
  return !stillLogin; // true = login succeeded
}

(async () => {
  console.log('\n=== Hikvision Camera Discovery & Login ===\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 400,
    args: ['--disable-web-security']
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  console.log('[1] Opening camera web interface...');
  await page.goto('http://192.168.29.157', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(3000);
  await ss(page, 'initial-page');

  const title = await page.title();
  console.log(`    Title: "${title}"`);

  // Check for Hikvision activation (brand new camera needs password set)
  const bodyText = await page.innerText('body').catch(() => '');
  console.log(`    Page preview: ${bodyText.substring(0, 200)}`);

  // Check if it's an activation page (no existing password)
  const isActivation = bodyText.toLowerCase().includes('activ') ||
    await page.$('.init_password, .activate, [id*="activate"]').then(el => !!el);

  if (isActivation) {
    console.log('\n[!] Activation required — setting new password...');
    // Hikvision activation: set admin password
    const NEW_PASS = 'Hik@12345';
    const pwInputs = await page.$$('input[type="password"]');
    for (const inp of pwInputs) {
      await inp.fill(NEW_PASS);
      await page.waitForTimeout(300);
    }
    await ss(page, 'activation-filled');
    const okBtn = await page.$('button:has-text("OK"), .confirm, input[type=submit]');
    if (okBtn) await okBtn.click();
    await page.waitForTimeout(3000);
    await ss(page, 'after-activation');
    console.log(`    Password set to: ${NEW_PASS}`);
  } else {
    console.log('\n[2] Trying credentials...');
    let loggedIn = false;
    for (const { user, pass } of CREDS) {
      // Reload login page fresh for each attempt
      await page.goto('http://192.168.29.157', { waitUntil: 'domcontentloaded', timeout: 10000 });
      await page.waitForTimeout(1500);

      console.log(`    Trying: ${user} / "${pass}" ...`);
      const ok = await tryLogin(page, user, pass);
      if (ok) {
        console.log(`\n  ✓ LOGIN SUCCESS with: ${user} / ${pass}`);
        await ss(page, `login-success-${user}-${pass || 'blank'}`);
        loggedIn = true;
        break;
      } else {
        console.log(`    ✗ Failed`);
        await ss(page, `login-fail-${user}-${pass || 'blank'}`);
      }
    }

    if (!loggedIn) {
      console.log('\n  [!] All default credentials failed.');
      console.log('  [!] Camera may need physical reset or has a custom password already set.');
      await ss(page, 'all-creds-failed');
      await browser.close();
      return;
    }
  }

  // ── Post-login: explore the camera interface ─────────────────────────────
  console.log('\n[3] Exploring camera interface...');
  await page.waitForTimeout(2000);
  await ss(page, 'dashboard-main');

  // Get all nav links/tabs
  const navItems = await page.$$eval('a, [class*="tab"], [class*="menu"], [class*="nav"]',
    els => els.slice(0, 20).map(e => ({
      text: (e.innerText || e.textContent || '').trim(),
      cls: e.className.substring(0, 60)
    })).filter(x => x.text.length > 0 && x.text.length < 40)
  );
  console.log('    Nav items found:', navItems.slice(0, 10));

  // Look for live view
  const liveView = await page.$('[class*="live"], [class*="preview"], [class*="realtime"]');
  if (liveView) {
    await liveView.click();
    await page.waitForTimeout(2000);
    await ss(page, 'live-view');
    console.log('    Live view opened');
  }

  // Check camera info page
  const configLinks = await page.$$('[class*="config"], [class*="setting"], [class*="system"]');
  if (configLinks[0]) {
    await configLinks[0].click();
    await page.waitForTimeout(2000);
    await ss(page, 'settings-page');
  }

  console.log('\n=== Setup complete! Camera is accessible. ===');
  console.log(`Camera URL: http://192.168.29.157`);

  await page.waitForTimeout(5000);
  await browser.close();
})();
