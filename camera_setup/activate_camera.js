const { chromium } = require('playwright');
const path = require('path');

const CAMERA_IP = '192.168.29.157';
const CAMERA_URL = `http://${CAMERA_IP}`;
const SS_DIR = path.join(__dirname, 'screenshots');
const NEW_PASSWORD = 'Admin@1234';  // Strong password for CP Plus (8+ chars, letters+numbers+symbol)

let ssCount = 0;
async function ss(page, name) {
  const file = path.join(SS_DIR, `${String(ssCount++).padStart(2,'0')}--${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`  [SCREENSHOT] ${file}`);
}

(async () => {
  console.log('\n=== CP Plus Camera Activation via Playwright ===\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 600,
    args: ['--disable-web-security', '--allow-running-insecure-content']
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 900 }
  });

  const page = await context.newPage();

  // ── Step 1: Load camera page ──────────────────────────────────────────────
  console.log(`[1] Navigating to ${CAMERA_URL} ...`);
  try {
    await page.goto(CAMERA_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
  } catch (e) {
    console.log('  [WARN] Slow load, continuing anyway...');
  }
  await page.waitForTimeout(3000);
  await ss(page, 'camera-initial-load');

  const pageTitle = await page.title();
  const pageContent = await page.content();
  console.log(`  Page title: "${pageTitle}"`);
  console.log(`  Page length: ${pageContent.length} chars`);

  // ── Step 2: Detect state ─────────────────────────────────────────────────
  // Check for activation/init page vs login page
  const bodyText = (await page.innerText('body').catch(() => '')).toLowerCase();
  console.log('\n[2] Detecting page state...');

  const isActivation = bodyText.includes('activ') || bodyText.includes('init') ||
                       bodyText.includes('initialize') || bodyText.includes('new password') ||
                       bodyText.includes('set password') || bodyText.includes('create') ||
                       await page.$('input[type="password"]').then(el => !!el);

  // Dump visible input fields
  const inputs = await page.$$eval('input', els => els.map(e => ({
    type: e.type, name: e.name, id: e.id,
    placeholder: e.placeholder, value: e.value
  })));
  console.log('  Inputs found:', JSON.stringify(inputs, null, 2));

  // Dump visible buttons
  const buttons = await page.$$eval('button, input[type=submit], input[type=button]', els =>
    els.map(e => ({ tag: e.tagName, type: e.type, text: e.innerText || e.value, id: e.id }))
  );
  console.log('  Buttons found:', JSON.stringify(buttons, null, 2));

  // ── Step 3: Handle activation ─────────────────────────────────────────────
  console.log('\n[3] Attempting activation / login...');

  // Try to find password fields
  const pwFields = await page.$$('input[type="password"]');
  console.log(`  Password fields: ${pwFields.length}`);

  if (pwFields.length >= 2) {
    // Activation page — needs new password + confirm
    console.log('  -> Activation mode: setting new password');
    await pwFields[0].fill(NEW_PASSWORD);
    await page.waitForTimeout(500);
    await pwFields[1].fill(NEW_PASSWORD);
    await page.waitForTimeout(500);
    if (pwFields[2]) {
      await pwFields[2].fill(NEW_PASSWORD);
      await page.waitForTimeout(500);
    }
    await ss(page, 'activation-filled');

    // Try submit
    const submitBtn = await page.$('button[type=submit], input[type=submit], .x-btn-text');
    if (submitBtn) {
      await submitBtn.click();
    } else {
      await page.keyboard.press('Enter');
    }
    await page.waitForTimeout(3000);
    await ss(page, 'after-activation-submit');
    console.log('  Activation submitted.');

  } else if (pwFields.length === 1) {
    // Login page — just one password field
    console.log('  -> Login mode: trying credentials');

    const userField = await page.$('input[type="text"], input[name*="user"], input[id*="user"], input[name*="name"]');
    if (userField) {
      await userField.triple_click?.() || await userField.click({ clickCount: 3 });
      await userField.fill('admin');
      await page.waitForTimeout(300);
    }
    await pwFields[0].fill(NEW_PASSWORD);
    await page.waitForTimeout(500);
    await ss(page, 'login-filled');

    const submitBtn = await page.$('button[type=submit], input[type=submit]');
    if (submitBtn) {
      await submitBtn.click();
    } else {
      await page.keyboard.press('Enter');
    }
    await page.waitForTimeout(3000);
    await ss(page, 'after-login');
  }

  // ── Step 4: Post-activation state ─────────────────────────────────────────
  await page.waitForTimeout(2000);
  await ss(page, 'final-state');
  const finalTitle = await page.title();
  const finalUrl = page.url();
  console.log(`\n[4] Final state:`);
  console.log(`  Title: "${finalTitle}"`);
  console.log(`  URL: ${finalUrl}`);

  // Dump all visible text for analysis
  const finalText = (await page.innerText('body').catch(() => '')).substring(0, 500);
  console.log(`  Page text preview: ${finalText}`);

  // ── Step 5: Try to navigate to live view ─────────────────────────────────
  console.log('\n[5] Looking for live view / stream...');
  const liveLinks = await page.$$eval('a, [class*="live"], [class*="preview"], [class*="video"]',
    els => els.slice(0, 10).map(e => ({ tag: e.tagName, text: e.innerText, href: e.href, cls: e.className }))
  );
  console.log('  Live view elements:', JSON.stringify(liveLinks, null, 2));

  await ss(page, 'live-view-check');

  console.log('\n=== Done. Check screenshots/ folder for visuals. ===');
  console.log(`=== Password set to: ${NEW_PASSWORD} ===\n`);

  await page.waitForTimeout(4000);
  await browser.close();
})();
