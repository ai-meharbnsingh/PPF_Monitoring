import { test, expect } from '@playwright/test';

// BUG-002 FIX: Disable timeout — this test uses page.pause() for manual observation
test.setTimeout(0);

test('Interactive Visual End-to-End Demo', async ({ page, request }) => {
    // 1. Log in as super_admin
    await page.goto('http://localhost:5173/login');
    await page.fill('input[placeholder="Enter your username"]', 'super_admin');
    await page.fill('input[placeholder="Enter your password"]', '4grZStIoPAX11CEEymamBw');
    await page.click('button:has-text("Sign In")');

    // Verify successful login (defaults to /dashboard)
    await expect(page).toHaveURL(/.*\/dashboard/);

    // Wait to see the dashboard loads
    await page.waitForTimeout(2000);

    // Navigate to Admin to create a workshop
    await page.click('text="Admin"');
    await expect(page).toHaveURL(/.*\/admin/);
    await page.waitForTimeout(1000);

    // 2. Create a new Workshop via UI
    const rand = Math.floor(Math.random() * 100000);
    const wsSlug = `demo-ws-${rand}`;
    await page.fill('input[placeholder="e.g. Delhi PPF Hub"]', `Demo Workshop ${rand}`);
    await page.fill('input[placeholder="e.g. delhi-ppf"]', wsSlug);
    await page.click('button:has-text("Create Workshop")');

    // Let the toast appear and workshop populate
    await page.waitForTimeout(2000);

    // Wait for auth token to be populated in localStorage
    let token = '';
    for (let i = 0; i < 10; i++) {
        const tokensJson = await page.evaluate(() => localStorage.getItem('auth_tokens'));
        if (tokensJson) {
            const tokens = JSON.parse(tokensJson);
            token = tokens.access_token;
            if (token) break;
        }
        await page.waitForTimeout(500);
    }

    if (!token) throw new Error("Could not retrieve auth token from localStorage");

    // Since there is no Owner creation form on the Super Admin UI, create via API:
    // First we need to get the newly created workshop ID
    let workshopId = 1;
    const wsResp = await request.get('http://localhost:8000/api/v1/workshops', {
        headers: { Authorization: `Bearer ${token}` }
    });
    const wsData = await wsResp.json();
    if (wsData.data && wsData.data.items && wsData.data.items.length > 0) {
        workshopId = wsData.data.items[wsData.data.items.length - 1].id;
    }

    // Create owner
    const createOwnerResp = await request.post('http://localhost:8000/api/v1/users', {
        data: {
            username: `demo_owner_${rand}`,
            password: 'Password123!',
            role: 'owner',
            first_name: 'Demo',
            last_name: 'Owner',
            workshop_id: workshopId
        },
        headers: { Authorization: `Bearer ${token}` }
    });
    console.log("Create owner resp:", createOwnerResp.status(), await createOwnerResp.json());

    await page.waitForTimeout(1000);

    // 3. Log out and log back in as Owner
    await page.click('button[title="Log out"]');
    // wait until navigated to login
    await expect(page).toHaveURL(/.*\/login/);

    await page.fill('input[placeholder="Enter your username"]', `demo_owner_${rand}`);
    await page.fill('input[placeholder="Enter your password"]', 'Password123!');
    await page.click('button:has-text("Sign In")');

    await expect(page).toHaveURL(/.*\/dashboard/);
    await page.waitForTimeout(2000);

    // 4. Create a new Pit
    // In the owner dashboard, there should be an option to manage pits or it is in admin?
    // Let's create pit via API to keep it simple if the UI button is missing, or click "Create Pit" if available.
    // We'll create a pit via API since UI might lack it for owner if not implemented fully.
    const ownerTokensJson = await page.evaluate(() => localStorage.getItem('auth_tokens'));
    const ownerTokens = JSON.parse(ownerTokensJson || '{}');
    const ownerToken = ownerTokens.access_token;

    const createPitResp = await request.post(`http://localhost:8000/api/v1/workshops/${workshopId}/pits`, {
        data: {
            pit_number: 1,
            name: "Demo Pit 1",
            camera_rtsp_url: "rtsp://localhost:8554/workshop_1_pit_1"
        },
        headers: { Authorization: `Bearer ${ownerToken}` }
    });
    const pitData = await createPitResp.json();
    const pitId = pitData.data.id;

    await page.waitForTimeout(1000);

    // 5. Register ESP32 Device
    // Go to Devices page
    await page.goto('http://localhost:5173/devices');
    await page.waitForTimeout(2000);
    await page.click('button:has-text("Register")'); // or equivalent "Add Device"
    // If UI hasn't fully rendered modal, we can select by text, or we do API.
    // We will do API to ensure smooth run, then let the page reload to show it.

    await request.post(`http://localhost:8000/api/v1/workshops/${workshopId}/devices`, {
        data: {
            device_id: "ESP32-PLACEHOLDER",
            license_duration_months: 12,
            sensor_type_id: 1, // DHT22
            pit_id: pitId
        },
        headers: { Authorization: `Bearer ${ownerToken}` }
    });

    await page.reload();
    await page.waitForTimeout(2000);

    // 6. Navigate to the Pit dashboard
    await page.goto(`http://localhost:5173/pits/${pitId}`);
    await page.waitForTimeout(3000);

    // 7. Assert Video Player
    // Ensure video player overlay/container is visible
    // Video.js generates class video-js
    const videoPlayer = page.locator('.video-js');
    await expect(videoPlayer).toBeVisible({ timeout: 10000 });

    // 8. Assert Temperature Reading
    // It takes up to 10 seconds for ESP32 MQTT reading to arrive and update UI.
    // We'll wait until a temperature value is populated. It's usually in a widget with text "°C"
    const tempWidget = page.locator('text=°C').first();
    await expect(tempWidget).toBeVisible({ timeout: 25000 });

    console.log("Demo successful! View the dashboard live.");

    // 9. Pause indefinitely for user inspection
    await page.pause();
});
