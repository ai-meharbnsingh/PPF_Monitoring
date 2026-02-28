/**
 * Playwright Test for Google Antigravity
 * Run with: npx playwright test scripts/antigravity-test.spec.js --headed
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

const CONFIG = {
  frontendUrl: process.env.FRONTEND_URL || 'https://ppf-monitoring.vercel.app',
  credentials: {
    username: 'super_admin',
    password: 'SuperAdmin@123'
  }
};

test.describe('PPF Monitoring - Team Page Workshop Dropdown Test', () => {
  
  test('Login and check workshop dropdown', async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ Console error: ${msg.text()}`);
      } else {
        console.log(`ℹ️  Console: ${msg.text()}`);
      }
    });

    // Step 1: Go to landing page
    console.log('📍 Step 1: Loading landing page...');
    await page.goto(CONFIG.frontendUrl);
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('01-landing-page.png');

    // Step 2: Click LOGIN
    console.log('📍 Step 2: Opening login modal...');
    await page.getByText('LOGIN').first().click();
    await page.waitForTimeout(1000);
    await expect(page).toHaveScreenshot('02-login-modal.png');

    // Step 3: Enter credentials
    console.log('📍 Step 3: Entering credentials...');
    const usernameInput = page.locator('input[type="text"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    
    await usernameInput.fill(CONFIG.credentials.username);
    await passwordInput.fill(CONFIG.credentials.password);
    await expect(page).toHaveScreenshot('03-credentials-entered.png');

    // Step 4: Submit
    console.log('📍 Step 4: Submitting login...');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForTimeout(3000);
    await expect(page).toHaveScreenshot('04-logged-in.png');

    // Step 5: Navigate to Team page
    console.log('📍 Step 5: Going to Team page...');
    await page.goto(`${CONFIG.frontendUrl}/admin/staff`);
    await page.waitForTimeout(2000);
    await expect(page).toHaveScreenshot('05-team-page.png');

    // Step 6: Click Add Member
    console.log('📍 Step 6: Opening Add Member modal...');
    await page.getByRole('button', { name: /add member/i }).click();
    await page.waitForTimeout(1500);
    await expect(page).toHaveScreenshot('06-add-member-modal.png');

    // Step 7: Check debug info
    console.log('📍 Step 7: Checking debug info...');
    const debugText = await page.locator('text=Role:').first().textContent().catch(() => 'Not found');
    console.log(`   Debug info: ${debugText}`);
    await expect(page).toHaveScreenshot('07-debug-info.png');

    // Step 8: Check for workshop elements
    console.log('📍 Step 8: Checking for workshop dropdown...');
    
    const workshopSelect = page.locator('select').first();
    const workshopLabel = page.getByText('Workshop', { exact: false }).first();
    const loadButton = page.getByText('Load/Refresh Workshops');
    
    const hasSelect = await workshopSelect.isVisible().catch(() => false);
    const hasLabel = await workshopLabel.isVisible().catch(() => false);
    const hasLoadButton = await loadButton.isVisible().catch(() => false);

    console.log(`   ✅ Select visible: ${hasSelect}`);
    console.log(`   ✅ Label visible: ${hasLabel}`);
    console.log(`   ✅ Load button visible: ${hasLoadButton}`);

    // Test report
    test.info().annotations.push({
      type: 'workshop-dropdown-check',
      description: `Select: ${hasSelect}, Label: ${hasLabel}, LoadBtn: ${hasLoadButton}`
    });

    // If load button exists, click it
    if (hasLoadButton) {
      console.log('📍 Step 9: Clicking Load Workshops...');
      await loadButton.click();
      await page.waitForTimeout(2000);
      await expect(page).toHaveScreenshot('08-after-load.png');

      // Check if dropdown appeared
      const hasSelectNow = await workshopSelect.isVisible().catch(() => false);
      console.log(`   Select now visible: ${hasSelectNow}`);
      
      if (hasSelectNow) {
        const options = await workshopSelect.locator('option').count();
        console.log(`   Number of options: ${options}`);
        
        // Open dropdown
        await workshopSelect.click();
        await page.waitForTimeout(500);
        await expect(page).toHaveScreenshot('09-dropdown-open.png');
      }
    }

    // Final state
    await page.waitForTimeout(2000);
    await expect(page).toHaveScreenshot('10-final-state.png');
    
    console.log('✅ Test completed successfully!');
  });
});
