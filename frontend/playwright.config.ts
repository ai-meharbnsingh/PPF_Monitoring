/**
 * playwright.config.ts
 * PPF Workshop Monitoring System — Playwright E2E Configuration
 *
 * Tests run against the Vite dev server at port 5175.
 * API calls are mocked via page.route() — no live backend required
 * for smoke tests. For full integration tests, spin up the Docker stack first.
 */

import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: 'http://localhost:5175',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // Starts the Vite dev server automatically if not already running
  webServer: {
    command: 'npm run dev -- --port 5175 --strictPort',
    port: 5175,
    reuseExistingServer: true,
    timeout: 60_000,
    cwd: '.',
  },
})
