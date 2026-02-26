import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 300 });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  const failedRequests: string[] = [];
  page.on('response', resp => {
    if (resp.url().includes('/api/') && resp.status() >= 400) {
      failedRequests.push(`${resp.status()} ${resp.url()}`);
    }
  });

  // 1. Login
  console.log('→ Login...');
  await page.goto('http://localhost:5173/login');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshots/debug/01-login.png', fullPage: true });

  await page.fill('input[name="username"]', 'owner');
  await page.fill('input[name="password"]', 'Owner@123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'screenshots/debug/02-after-login.png', fullPage: true });
  console.log('  URL:', page.url());

  // 2. Dashboard
  console.log('→ Dashboard...');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'screenshots/debug/03-dashboard.png', fullPage: true });

  // 3. Pit detail
  console.log('→ Pit detail...');
  await page.goto('http://localhost:5173/admin/pits/10');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: 'screenshots/debug/05-pit-detail.png', fullPage: true });

  // Print errors
  console.log('\n=== Console Errors ===');
  consoleErrors.forEach(e => console.log('  ', e));
  console.log('\n=== Failed API Requests ===');
  failedRequests.forEach(r => console.log('  ', r));

  console.log('\n→ Done!');
  await browser.close();
})();
