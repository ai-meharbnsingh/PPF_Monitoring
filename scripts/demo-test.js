#!/usr/bin/env node
/**
 * Playwright Demo - Shows the workshop dropdown issue
 * Run: node scripts/demo-test.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const CONFIG = {
  // url: 'https://ppf-monitoring.vercel.app',
  url: 'http://localhost:5173', // LOCAL TESTING
  username: 'super_admin',
  password: 'SuperAdmin@123',
  screenshotsDir: path.join(__dirname, '..', 'demo-screenshots')
};

async function delay(ms) {
  console.log(`   ⏳ Waiting ${ms}ms...`);
  return new Promise(r => setTimeout(r, ms));
}

async function takeScreenshot(page, name) {
  const filepath = path.join(CONFIG.screenshotsDir, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`   📸 Screenshot saved: ${filepath}`);
  return filepath;
}

async function runDemo() {
  console.log('╔════════════════════════════════════════════════════════╗');
  console.log('║     PPF Monitoring - Playwright Demo Test              ║');
  console.log('║     Checking Workshop Dropdown in Add Member           ║');
  console.log('╚════════════════════════════════════════════════════════╝\n');

  // Create screenshots directory
  if (!fs.existsSync(CONFIG.screenshotsDir)) {
    fs.mkdirSync(CONFIG.screenshotsDir, { recursive: true });
  }

  console.log('🚀 Launching browser (headed mode - you will see it)...\n');
  
  const browser = await chromium.launch({ 
    headless: false,  // FALSE = you can see the browser
    slowMo: 800,      // Slow down for visibility
    args: ['--window-size=1400,900']
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordVideo: {
      dir: CONFIG.screenshotsDir,
      size: { width: 1400, height: 900 }
    }
  });

  const page = await context.newPage();

  // Capture console logs
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`   🔴 Console Error: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Navigate to landing page
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 1: Loading landing page');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    await page.goto(CONFIG.url);
    await page.waitForLoadState('networkidle');
    await takeScreenshot(page, '01-landing-page');
    console.log('   ✅ Landing page loaded\n');

    // Step 2: Click LOGIN
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 2: Clicking LOGIN button');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    await page.getByText('LOGIN').first().click();
    await delay(1000);
    await takeScreenshot(page, '02-login-modal');
    console.log('   ✅ Login modal opened\n');

    // Step 3: Enter credentials
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 3: Entering super_admin credentials');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`   Username: ${CONFIG.username}`);
    console.log(`   Password: ${CONFIG.password}`);
    
    await page.locator('input[type="text"]').first().fill(CONFIG.username);
    await page.locator('input[type="password"]').first().fill(CONFIG.password);
    await takeScreenshot(page, '03-credentials-filled');
    console.log('   ✅ Credentials entered\n');

    // Step 4: Submit login
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 4: Submitting login form');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    await page.getByRole('button', { name: /sign in/i }).click();
    await delay(3000);
    await takeScreenshot(page, '04-after-login');
    console.log('   ✅ Logged in\n');

    // Step 5: Navigate to Team page
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 5: Navigating to Team page');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    // Try clicking Team link or navigate directly
    const teamLink = page.locator('a[href*="staff"], a:has-text("Team")').first();
    if (await teamLink.isVisible().catch(() => false)) {
      await teamLink.click();
    } else {
      await page.goto(`${CONFIG.url}/admin/staff`);
    }
    await delay(2000);
    await takeScreenshot(page, '05-team-page');
    console.log('   ✅ Team page loaded\n');

    // Step 6: Click Add Member
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 6: Clicking "Add Member" button');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    await page.getByRole('button', { name: /add member/i }).first().click();
    await delay(1500);
    await takeScreenshot(page, '06-add-member-modal');
    console.log('   ✅ Add Member modal opened\n');

    // Step 7: Check debug info
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 7: Reading debug info from yellow box');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    const debugBox = page.locator('div:has-text("DEBUG INFO:")').first();
    const debugVisible = await debugBox.isVisible().catch(() => false);
    
    if (debugVisible) {
      const debugText = await debugBox.textContent();
      console.log('\n   📝 DEBUG INFO FOUND:\n');
      console.log('   ' + debugText.split('\n').join('\n   '));
    } else {
      console.log('   ⚠️  Debug box not found');
    }
    await takeScreenshot(page, '07-debug-info');
    console.log('');

    // Step 8: Check for workshop dropdown
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 8: Checking for Workshop dropdown');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    const workshopLabel = page.getByText('Workshop *', { exact: false });
    const workshopSelect = page.locator('select').first();
    const loadButton = page.getByText('Load/Refresh Workshops');
    
    const hasLabel = await workshopLabel.isVisible().catch(() => false);
    const hasSelect = await workshopSelect.isVisible().catch(() => false);
    const hasLoadBtn = await loadButton.isVisible().catch(() => false);

    console.log(`\n   🔍 CHECK RESULTS:`);
    console.log(`   ├── Workshop label visible: ${hasLabel ? '✅ YES' : '❌ NO'}`);
    console.log(`   ├── Select dropdown visible: ${hasSelect ? '✅ YES' : '❌ NO'}`);
    console.log(`   └── Load button visible: ${hasLoadBtn ? '✅ YES' : '❌ NO'}`);

    // Step 9: Try to click Load Workshops
    if (hasLoadBtn) {
      console.log('\n   🔄 Clicking "Load/Refresh Workshops"...');
      await loadButton.click();
      await delay(2000);
      await takeScreenshot(page, '08-after-load-workshops');
      
      const hasSelectNow = await workshopSelect.isVisible().catch(() => false);
      console.log(`   Select now visible: ${hasSelectNow ? '✅ YES' : '❌ NO'}`);
      
      if (hasSelectNow) {
        const options = await workshopSelect.locator('option').count();
        console.log(`   Number of workshop options: ${options}`);
        
        // Try to open dropdown
        await workshopSelect.click();
        await delay(500);
        await takeScreenshot(page, '09-dropdown-opened');
      }
    }

    // Final screenshot
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📍 STEP 9: Final state');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    await delay(1000);
    await takeScreenshot(page, '10-final-state');

    // Summary
    console.log('\n╔════════════════════════════════════════════════════════╗');
    console.log('║                    DEMO COMPLETE                       ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');
    console.log(`📁 Screenshots saved to: ${CONFIG.screenshotsDir}`);
    console.log(`🎥 Video recorded in: ${CONFIG.screenshotsDir}\n`);

    // List files
    const files = fs.readdirSync(CONFIG.screenshotsDir);
    console.log('📂 Files created:');
    files.forEach(f => console.log(`   - ${f}`));

    // Keep browser open for inspection
    console.log('\n⏳ Keeping browser open for 15 seconds for manual inspection...');
    console.log('   (You can interact with the page)');
    await delay(15000);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, 'error.png'),
      fullPage: true 
    });
  } finally {
    await context.close();
    await browser.close();
    console.log('\n👋 Browser closed. Demo complete!');
  }
}

// Run the demo
runDemo().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
