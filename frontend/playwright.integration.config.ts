/**
 * playwright.integration.config.ts
 * PPF Workshop Monitoring System — Real Integration Test Config
 *
 * Runs HEADED against a live stack:
 *   ✅ FastAPI backend  → http://localhost:8000
 *   ✅ PostgreSQL       → localhost:5432  (real data persisted)
 *   ✅ Mosquitto MQTT   → localhost:1883  (live sensor data)
 *   ✅ Vite frontend    → http://localhost:5175
 *   ⚠️  MediaMTX        → NOT running (no Docker) — camera shows "offline"
 *
 * Run:
 *   npx playwright test --config playwright.integration.config.ts
 *
 * Seeds (already applied):
 *   owner_amit  / Owner2026   (role=owner,  workshop_id=1)
 *   staff_raj   / Staff2026   (role=staff,  workshop_id=1)
 *   Pit 10 "Demo Pit 1" with live ESP32 sensor data
 */
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/integration-real.spec.ts',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-integration', open: 'always' }],
  ],
  use: {
    baseURL: 'http://localhost:5175',
    headless: false,         // ← HEADED: watch the real browser
    slowMo: 600,             // ← 600 ms between actions so you can follow along
    trace: 'on',
    screenshot: 'on',
    video: 'on',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    viewport: { width: 1280, height: 800 },
  },
  projects: [
    {
      name: 'chromium-integration',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // No webServer block — frontend + backend must be running manually before test
})
