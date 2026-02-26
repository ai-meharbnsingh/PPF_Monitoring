import { chromium } from 'playwright'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BASE = 'http://localhost:5173'
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots', 'responsive')

const VIEWPORTS = [
  { name: 'desktop-1920', width: 1920, height: 1080 },
  { name: 'laptop-1366', width: 1366, height: 768 },
  { name: 'tablet-1024', width: 1024, height: 768 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'mobile-425', width: 425, height: 900 },
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'mobile-320', width: 320, height: 568 },
]

async function run() {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })

  const browser = await chromium.launch({ headless: true })

  for (const vp of VIEWPORTS) {
    console.log(`\n--- Testing ${vp.name} (${vp.width}x${vp.height}) ---`)
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } })
    const page = await context.newPage()

    // Login
    await page.goto(`${BASE}/login`)
    await page.waitForTimeout(1000)
    await page.fill('input[placeholder*="username" i], input[name="username"], input[type="text"]', 'super_admin')
    await page.fill('input[type="password"]', 'User@123')
    await page.click('button[type="submit"]')
    await page.waitForTimeout(3000)

    // Should be on dashboard now
    await page.goto(`${BASE}/admin/dashboard`)
    await page.waitForTimeout(3000)

    // Full page screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, `dashboard--${vp.name}.png`),
      fullPage: true,
    })
    console.log(`  Captured: dashboard--${vp.name}.png`)

    // Scroll down and capture if page is long
    const pageHeight = await page.evaluate(() => document.body.scrollHeight)
    if (pageHeight > vp.height) {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
      await page.waitForTimeout(500)
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `dashboard--${vp.name}--scrolled.png`),
        fullPage: false,
      })
      console.log(`  Captured: dashboard--${vp.name}--scrolled.png`)
    }

    await context.close()
  }

  await browser.close()
  console.log(`\nAll screenshots saved to: ${SCREENSHOT_DIR}`)
}

run().catch(console.error)
