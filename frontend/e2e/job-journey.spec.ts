/**
 * e2e/job-journey.spec.ts
 * PPF Workshop Monitoring System — UI Smoke Tests
 *
 * Tests the complete customer-visible journey:
 *   1. Login page renders correctly
 *   2. Login with mocked credentials → redirects to dashboard
 *   3. Navigate to /jobs → open Create Job modal → fill + submit
 *   4. Job detail page shows vehicle info + "Copy Tracking Link" button
 *   5. Public tracking page (/track/:token) renders without auth
 *   6. Invalid tracking token shows "Job not found" message
 *
 * All API calls are mocked via page.route() — no live backend required.
 * Run:   npx playwright test
 * Debug: npx playwright test --headed --slowMo 300
 *
 * ─── Bug #001 (found during test authoring) ──────────────────────────────────
 * Task 1.G.18 ("Assign staff to job — Staff dropdown in JobDetailPage") is
 * listed as ✅ in PROJECT_TASKS.md, but the JobDetailPage sidebar contains no
 * staff-assignment dropdown or modal. The API (PATCH /jobs/:id/assign-staff)
 * exists. A future wave should add the UI component.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { test, expect, type Page, type Route } from '@playwright/test'

// ─── Base URL for the backend API (same as apiClient.baseURL) ─────────────────
const API = 'http://localhost:8000/api/v1'

// ─── Shared mock data ─────────────────────────────────────────────────────────

const MOCK_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.mock'

const MOCK_USER = {
  id: 1,
  username: 'owner_demo',
  email: 'owner@demo.ppf',
  first_name: 'Demo',
  last_name: 'Owner',
  role: 'owner' as const,
  workshop_id: 1,
  is_temporary_password: false,
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
}

const MOCK_PIT = {
  id: 10,
  workshop_id: 1,
  name: 'Pit 1',
  display_name: 'Pit 1 — Bay A',
  status: 'available',
  camera_is_online: false,
  created_at: '2026-01-01T00:00:00Z',
}

const FUTURE_ISO = new Date(Date.now() + 3 * 3600 * 1000).toISOString()

const MOCK_JOB_DETAIL = {
  id: 42,
  workshop_id: 1,
  pit_id: 10,
  pit_name: 'Pit 1',
  work_type: 'Full PPF',
  car_model: 'Honda City',
  car_plate: 'DL 01 AB 1234',
  car_color: 'Pearl White',
  car_year: null,
  status: 'waiting',
  quoted_price: 25000,
  currency: 'INR',
  customer_view_token: 'TRK-DEMO-9999',
  customer: {
    id: 5,
    username: 'cust_ravi',
    first_name: 'Ravi',
    last_name: 'Kumar',
    email: null,
    phone: '+91 98765 43210',
  },
  assigned_staff: null,
  owner_notes: null,
  work_description: null,
  scheduled_start_time: null,
  actual_start_time: null,
  estimated_end_time: FUTURE_ISO,
  actual_end_time: null,
  estimated_duration_minutes: 180,
  status_history: [],
  created_at: '2026-02-23T10:00:00Z',
}

const MOCK_JOB_SUMMARY = {
  id: 42,
  workshop_id: 1,
  pit_id: 10,
  pit_name: 'Pit 1',
  car_model: 'Honda City',
  car_plate: 'DL 01 AB 1234',
  work_type: 'Full PPF',
  status: 'waiting',
  quoted_price: 25000,
  currency: 'INR',
  scheduled_start_time: null,
  actual_start_time: null,
  estimated_end_time: FUTURE_ISO,
  actual_end_time: null,
  created_at: '2026-02-23T10:00:00Z',
  customer_name: 'Ravi Kumar',
}

const MOCK_TRACKING_JOB = {
  id: 42,
  work_type: 'Full PPF',
  car_model: 'Honda City',
  car_plate: 'DL 01 AB 1234',
  status: 'in_progress',
  workshop_name: 'Demo Workshop',
  pit_display_name: 'Pit 1 — Bay A',
  estimated_end_time: FUTURE_ISO,
  scheduled_start_time: null,
  actual_start_time: new Date().toISOString(),
  actual_end_time: null,
}

// ─── Helper: seed localStorage to bypass the login UI ────────────────────────
async function seedAuth(page: Page): Promise<void> {
  await page.addInitScript(
    ({
      token,
      user,
      tokenKey,
      userKey,
    }: {
      token: string
      user: object
      tokenKey: string
      userKey: string
    }) => {
      localStorage.setItem(tokenKey, token)
      localStorage.setItem(userKey, JSON.stringify(user))
    },
    { token: MOCK_TOKEN, user: MOCK_USER, tokenKey: 'ppf_token', userKey: 'ppf_user' },
  )
}

// ─── Helper: mock routes that every authenticated page needs ─────────────────
async function mockCommonRoutes(page: Page): Promise<void> {
  // /auth/me — backend wraps response in { success: true, data: UserProfile }
  await page.route(`${API}/auth/me`, (r: Route) =>
    r.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: MOCK_USER }),
    }),
  )

  // WebSocket — abort silently so WS errors don't block tests
  await page.route('**/ws**', (r: Route) => r.abort())

  // Pits list — pitsApi.listPits() calls GET /workshops/:id/pits and returns resp.data
  // directly (plain array, not paginated). DashboardPage dispatches setPits(pitList).
  await page.route(`${API}/workshops/1/pits*`, (r: Route) =>
    r.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([MOCK_PIT]),
    }),
  )

  // Latest sensor data — sensorsApi.latestForWorkshop calls /workshops/:id/sensors/latest
  await page.route(`${API}/workshops/*/sensors/latest`, (r: Route) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) }),
  )

  // Alerts — loaded by AlertBell in the Topbar
  await page.route(`${API}/workshops/*/alerts*`, (r: Route) =>
    r.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
        total_pages: 0,
        has_next: false,
        has_prev: false,
      }),
    }),
  )
}

// ═════════════════════════════════════════════════════════════════════════════
// SMOKE TESTS — UI JOURNEY
// ═════════════════════════════════════════════════════════════════════════════

test.describe('PPF Dashboard — UI Smoke Tests (Phase 1-H)', () => {
  // ── [AC-1] Login page renders all expected elements ───────────────────────
  test('1 · Login page renders username + password fields and Sign In button', async ({
    page,
  }) => {
    await page.goto('/login')

    await expect(page.locator('h1')).toContainText('PPF Monitor')
    await expect(page.getByPlaceholder('Enter your username')).toBeVisible()
    await expect(page.getByPlaceholder('Enter your password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible()
    await expect(page.getByText('PPF Workshop Monitoring System')).toBeVisible()
  })

  // ── [AC-2] Login shows error on bad credentials ────────────────────────────
  test('2 · Login shows error message when credentials are rejected (401)', async ({ page }) => {
    await page.route(`${API}/auth/login`, (r: Route) =>
      r.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      }),
    )
    await page.route('**/ws**', (r: Route) => r.abort())

    await page.goto('/login')
    await page.getByPlaceholder('Enter your username').fill('wrong_user')
    await page.getByPlaceholder('Enter your password').fill('wrong_pass')
    await page.getByRole('button', { name: 'Sign In' }).click()

    // Error message appears — the login error div is always present when error is set
    // (it renders a <p> inside a red-themed div on the login form)
    await expect(
      page.locator('p.text-sm.text-red-400, [class*="text-red"]').first()
    ).toBeVisible({ timeout: 8000 })
  })

  // ── [AC-3] Successful login → dashboard ───────────────────────────────────
  test('3 · Login with valid credentials → redirects to /dashboard', async ({ page }) => {
    // Backend wraps login response: { success: true, data: { access_token, token_type } }
    await page.route(`${API}/auth/login`, (r: Route) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { access_token: MOCK_TOKEN, token_type: 'bearer' },
        }),
      }),
    )
    await mockCommonRoutes(page)

    await page.goto('/login')
    await page.getByPlaceholder('Enter your username').fill('super_admin')
    await page.getByPlaceholder('Enter your password').fill('Demo@2026!')
    await page.getByRole('button', { name: 'Sign In' }).click()

    await page.waitForURL('**/dashboard', { timeout: 10_000 })
    // Dashboard heading should be visible
    await expect(page.getByRole('heading', { name: /workshop/i }).or(
      page.locator('h1')
    ).first()).toBeVisible()
  })

  // ── [AC-4] Jobs page — Create New Job modal ───────────────────────────────
  test('4 · Jobs page → Create Job modal → fill form → job appears in list', async ({
    page,
  }) => {
    await seedAuth(page)
    await mockCommonRoutes(page)

    // Jobs list — initially empty; after POST returns the new job
    let created = false
    await page.route(`${API}/workshops/1/jobs*`, async (r: Route) => {
      if (r.request().method() === 'GET') {
        const items = created ? [MOCK_JOB_SUMMARY] : []
        await r.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items,
            total: items.length,
            page: 1,
            page_size: 20,
            total_pages: items.length > 0 ? 1 : 0,
            has_next: false,
            has_prev: false,
          }),
        })
      } else if (r.request().method() === 'POST') {
        created = true
        await r.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_JOB_DETAIL),
        })
      } else {
        await r.continue()
      }
    })

    // Visit dashboard first so DashboardPage fetches pits → populates Redux pits slice.
    // IMPORTANT: We MUST use client-side (React Router) navigation to /jobs afterwards,
    // NOT page.goto('/jobs'), because page.goto() causes a full HTML reload which
    // re-initialises the Redux store from scratch, discarding the loaded pits.
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')

    // Client-side navigate to /jobs via the sidebar link (keeps React SPA and Redux store alive)
    await page.getByRole('link', { name: /^jobs$/i }).click()
    await page.waitForURL('**/jobs')
    await expect(page.locator('h1')).toContainText('Jobs')

    // Click "New Job" button — there may be a desktop + mobile version; use first visible
    await page.getByRole('button', { name: /new job/i }).first().click()

    // Modal opens
    await expect(page.getByText('Create New Job')).toBeVisible()

    // Select pit — the first <select> in the modal (Pit 1 is now in the store)
    const pitSelect = page.locator('select').first()
    await pitSelect.selectOption({ label: 'Pit 1' })

    // Select work type — second <select>
    const workTypeSelect = page.locator('select').nth(1)
    await workTypeSelect.selectOption({ index: 1 })

    // Fill car details
    await page.getByPlaceholder('e.g. Honda City').fill('Honda City')
    await page.getByPlaceholder('e.g. MH12AB1234').fill('DL 01 AB 1234')

    // Fill customer name
    await page.getByPlaceholder('Full name').fill('Ravi Kumar')

    // Submit
    await page.getByRole('button', { name: 'Create Job' }).click()

    // Job appears in list — car model should be visible
    await expect(page.getByText('Honda City')).toBeVisible({ timeout: 5000 })
  })

  // ── [AC-5] Job detail page — tracking link is present ────────────────────
  test('5 · Job detail page shows vehicle info + "Copy Tracking Link" button', async ({
    page,
  }) => {
    await seedAuth(page)
    await mockCommonRoutes(page)

    await page.route(`${API}/jobs/42`, (r: Route) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_JOB_DETAIL),
      }),
    )

    await page.goto('/jobs/42')

    // Vehicle section — heading contains car model, Vehicle sidebar contains model again
    await expect(page.getByRole('heading', { name: 'Honda City' })).toBeVisible()
    // Plate appears in a <dd> or <span class="font-mono">
    await expect(page.locator('text=DL 01 AB 1234').first()).toBeVisible()

    // "Customer Tracking" section with copy button
    await expect(page.getByText('Customer Tracking')).toBeVisible()
    await expect(page.getByRole('button', { name: /copy tracking link/i })).toBeVisible()
  })

  // ── [AC-6] Job detail — Copy Tracking Link writes correct URL ─────────────
  test('6 · Copy Tracking Link writes /track/<token> to clipboard', async ({
    page,
    context,
  }) => {
    await seedAuth(page)
    await mockCommonRoutes(page)

    await page.route(`${API}/jobs/42`, (r: Route) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_JOB_DETAIL),
      }),
    )

    // Grant clipboard permission
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])

    await page.goto('/jobs/42')
    await expect(page.getByRole('button', { name: /copy tracking link/i })).toBeVisible()
    await page.getByRole('button', { name: /copy tracking link/i }).click()

    // Button text changes to "Copied!"
    await expect(page.getByRole('button', { name: /copied!/i })).toBeVisible({ timeout: 3000 })

    // Clipboard contains the correct URL
    const clipText: string = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipText).toContain('/track/TRK-DEMO-9999')
  })

  // ── [AC-7] Public tracking page — renders without authentication ───────────
  test('7 · Customer tracking page (/track/:token) renders vehicle + progress', async ({
    page,
  }) => {
    // Public page — NO seedAuth, NO Authorization header
    await page.route(`${API}/track/TRK-DEMO-9999`, (r: Route) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_TRACKING_JOB),
      }),
    )
    // The tracking client calls http://localhost:8000/api/v1/track/... directly
    // (no Vite proxy). Playwright intercepts at the network level regardless.

    await page.goto('/track/TRK-DEMO-9999')

    // Wait for data to load (no spinner visible)
    await expect(page.getByText('Your Vehicle')).toBeVisible({ timeout: 8000 })

    // Vehicle info
    await expect(page.getByText('Honda City')).toBeVisible()
    await expect(page.getByText('DL 01 AB 1234')).toBeVisible()
    await expect(page.getByText('Full PPF')).toBeVisible()

    // Progress stepper section — use heading role to avoid matching "In Progress" badge
    await expect(page.getByRole('heading', { name: 'Progress' })).toBeVisible()

    // Auto-refresh notice
    await expect(page.getByText(/auto-refresh/i)).toBeVisible()
  })

  // ── [AC-8] Public tracking page — 404 token shows "Job not found" ─────────
  test('8 · Invalid tracking token shows "Job not found" message', async ({ page }) => {
    await page.route(`${API}/track/*`, (r: Route) =>
      r.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Job not found' }),
      }),
    )

    await page.goto('/track/INVALID-TOKEN-XYZ')

    await expect(page.getByText('Job not found')).toBeVisible({ timeout: 8000 })
    await expect(
      page.getByText(/invalid or has expired/i),
    ).toBeVisible()
  })

  // ── [BC-001] Bug: Staff assignment UI missing on Job Detail ───────────────
  test.skip(
    '9 · [BUG-001] Assign Staff dropdown visible on Job Detail page',
    async ({ page }) => {
      /**
       * BUG #001 — Task 1.G.18 listed as ✅ but no staff assignment UI exists.
       *
       * Expected: A staff dropdown / modal on /jobs/:id that calls
       *           PATCH /api/v1/jobs/:id/assign-staff
       *
       * Actual: JobDetailPage sidebar has Customer card, Tracking Link card,
       *         and Vehicle card — but no staff assignment component.
       *
       * Resolution: Add a StaffAssignDropdown component to the sidebar,
       *             populated by GET /workshops/:id/users?role=staff.
       *             Update PROJECT_TASKS.md when fixed.
       */
      await seedAuth(page)
      await mockCommonRoutes(page)
      await page.route(`${API}/jobs/42`, (r: Route) =>
        r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_JOB_DETAIL) }),
      )
      await page.goto('/jobs/42')
      await expect(page.getByText('Assigned Staff')).toBeVisible()
    },
  )
})
