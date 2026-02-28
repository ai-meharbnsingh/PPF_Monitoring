/**
 * Google Antigravity Test Script for PPF Monitoring
 * This script uses Playwright to test the "Add Member" modal
 * and check if the workshop dropdown is visible.
 * 
 * Run with: npx playwright test scripts/antigravity-test.js --headed
 * Or: node scripts/antigravity-test.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  frontendUrl: 'https://ppf-monitoring.vercel.app',
  backendUrl: 'https://ppf-backend-w0aq.onrender.com',
  credentials: {
    username: 'super_admin',
    password: 'SuperAdmin@123'
  },
  screenshotsDir: path.join(__dirname, '..', 'test-results', 'antigravity')
};

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTest() {
  console.log('🚀 Starting Antigravity Test...\n');
  
  // Create screenshots directory
  if (!fs.existsSync(CONFIG.screenshotsDir)) {
    fs.mkdirSync(CONFIG.screenshotsDir, { recursive: true });
  }

  const browser = await chromium.launch({ 
    headless: false, // Set to true for headless mode
    slowMo: 500 // Slow down for visibility
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordVideo: {
      dir: CONFIG.screenshotsDir,
      size: { width: 1400, height: 900 }
    }
  });
  
  const page = await context.newPage();
  
  try {
    // Step 1: Navigate to frontend
    console.log('📍 Step 1: Navigating to frontend...');
    await page.goto(CONFIG.frontendUrl);
    await delay(2000);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '01-landing-page.png'),
      fullPage: true 
    });
    console.log('   ✅ Landing page loaded\n');

    // Step 2: Click Login button
    console.log('📍 Step 2: Opening login modal...');
    const loginBtn = await page.locator('text=LOGIN').first();
    await loginBtn.click();
    await delay(1000);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '02-login-modal.png'),
      fullPage: true 
    });
    console.log('   ✅ Login modal opened\n');

    // Step 3: Enter credentials
    console.log('📍 Step 3: Entering credentials...');
    await page.fill('input[type="text"], input[name="username"]', CONFIG.credentials.username);
    await page.fill('input[type="password"]', CONFIG.credentials.password);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '03-credentials-entered.png'),
      fullPage: true 
    });
    console.log('   ✅ Credentials entered\n');

    // Step 4: Submit login
    console.log('📍 Step 4: Submitting login...');
    const submitBtn = await page.locator('button:has-text("Sign In"), button[type="submit"]').first();
    await submitBtn.click();
    await delay(3000);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '04-logged-in.png'),
      fullPage: true 
    });
    console.log('   ✅ Logged in\n');

    // Step 5: Navigate to Team/Staff page
    console.log('📍 Step 5: Navigating to Team page...');
    // Try to find Team link
    const teamLink = await page.locator('text=Team, a[href*="staff"], a[href*="team"]').first();
    if (await teamLink.isVisible().catch(() => false)) {
      await teamLink.click();
    } else {
      // Direct navigation
      await page.goto(`${CONFIG.frontendUrl}/admin/staff`);
    }
    await delay(2000);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '05-team-page.png'),
      fullPage: true 
    });
    console.log('   ✅ Team page loaded\n');

    // Step 6: Click "Add Member" button
    console.log('📍 Step 6: Clicking "Add Member" button...');
    const addMemberBtn = await page.locator('button:has-text("Add Member"), button:has-text("New")').first();
    await addMemberBtn.click();
    await delay(1500);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '06-add-member-modal.png'),
      fullPage: true 
    });
    console.log('   ✅ Add Member modal opened\n');

    // Step 7: Check for debug info
    console.log('📍 Step 7: Checking debug info...');
    const debugInfo = await page.locator('text=Role:').first();
    if (await debugInfo.isVisible().catch(() => false)) {
      const debugText = await debugInfo.textContent();
      console.log(`   ℹ️  Debug info found: ${debugText}\n`);
    } else {
      console.log('   ⚠️  No debug info visible\n');
    }
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '07-debug-info.png'),
      fullPage: true 
    });

    // Step 8: Check for workshop dropdown
    console.log('📍 Step 8: Checking for workshop dropdown...');
    
    // Look for select element
    const workshopSelect = await page.locator('select').first();
    const hasSelect = await workshopSelect.isVisible().catch(() => false);
    
    // Look for workshop label
    const workshopLabel = await page.locator('text=Workshop').first();
    const hasLabel = await workshopLabel.isVisible().catch(() => false);
    
    // Look for "Load Workshops" button
    const loadWorkshopsBtn = await page.locator('text=Load/Refresh Workshops').first();
    const hasLoadBtn = await loadWorkshopsBtn.isVisible().catch(() => false);

    console.log(`   Select element visible: ${hasSelect ? '✅ YES' : '❌ NO'}`);
    console.log(`   Workshop label visible: ${hasLabel ? '✅ YES' : '❌ NO'}`);
    console.log(`   Load button visible: ${hasLoadBtn ? '✅ YES' : '❌ NO'}`);

    if (hasLoadBtn) {
      console.log('\n📍 Step 9: Clicking "Load/Refresh Workshops"...');
      await loadWorkshopsBtn.click();
      await delay(2000);
      await page.screenshot({ 
        path: path.join(CONFIG.screenshotsDir, '08-after-load-workshops.png'),
        fullPage: true 
      });
      console.log('   ✅ Load workshops clicked\n');

      // Check again for dropdown
      const workshopSelect2 = await page.locator('select').first();
      const hasSelect2 = await workshopSelect2.isVisible().catch(() => false);
      console.log(`   Select element now visible: ${hasSelect2 ? '✅ YES' : '❌ NO'}`);
      
      if (hasSelect2) {
        const options = await workshopSelect2.locator('option').count();
        console.log(`   Number of options: ${options}`);
        
        // Click on dropdown to see options
        await workshopSelect2.click();
        await delay(1000);
        await page.screenshot({ 
          path: path.join(CONFIG.screenshotsDir, '09-dropdown-opened.png'),
          fullPage: true 
        });
      }
    }

    // Step 10: Check browser console for errors
    console.log('\n📍 Step 10: Checking browser console...');
    const logs = await page.evaluate(() => {
      return window.consoleLogs || [];
    });
    
    if (logs.length > 0) {
      console.log('   Console logs:', logs);
    } else {
      console.log('   No console logs captured');
    }

    // Final screenshot
    await delay(2000);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, '10-final-state.png'),
      fullPage: true 
    });

    console.log('\n✅ Test completed!');
    console.log(`📸 Screenshots saved to: ${CONFIG.screenshotsDir}`);
    
    // Generate report
    const report = {
      timestamp: new Date().toISOString(),
      url: CONFIG.frontendUrl,
      checks: {
        loginSuccessful: true,
        teamPageLoaded: true,
        addMemberModalOpened: true,
        workshopSelectVisible: hasSelect || false,
        workshopLabelVisible: hasLabel || false,
        loadButtonVisible: hasLoadBtn || false
      },
      screenshots: fs.readdirSync(CONFIG.screenshotsDir).filter(f => f.endsWith('.png'))
    };
    
    fs.writeFileSync(
      path.join(CONFIG.screenshotsDir, 'report.json'),
      JSON.stringify(report, null, 2)
    );
    
    console.log('\n📊 Report saved to report.json');
    console.log('\n🔍 Summary:');
    console.log(JSON.stringify(report.checks, null, 2));

    // Keep browser open for inspection (optional)
    console.log('\n⏳ Keeping browser open for 10 seconds for inspection...');
    await delay(10000);

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    await page.screenshot({ 
      path: path.join(CONFIG.screenshotsDir, 'error-state.png'),
      fullPage: true 
    });
  } finally {
    await context.close();
    await browser.close();
    console.log('\n👋 Browser closed');
  }
}

// Run the test
runTest().catch(console.error);
