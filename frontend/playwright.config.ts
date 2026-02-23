import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Both tests/ (interactive demos) and e2e/ (live E2E flows) are scanned
  testMatch: ['tests/**/*.spec.ts', 'e2e/**/*.spec.ts'],
  fullyParallel: false,
  forbidOnly: false,
  retries: 0,
  workers: 1,
  reporter: 'line',
  use: {
    trace: 'on-first-retry',
    launchOptions: {
      slowMo: 500,
      headless: false,
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
