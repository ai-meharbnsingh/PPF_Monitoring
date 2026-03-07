# 🔧 Intermittent Login Issue - Root Cause Analysis & Fix

## Problem
Login works sometimes but not others on https://ppf-monitoring.vercel.app

## Root Causes Identified

### 1. 🚨 PRIMARY: Render Free Tier Sleeping (CRITICAL)
```yaml
File: render.yaml
Issue: plan: free
```

**What happens:**
- Render free tier services **sleep after 15 minutes of inactivity**
- When you try to login after sleep, backend takes **30-60 seconds** to wake up
- Vercel/frontend timeouts before backend responds
- Results in: "Network Error" or login hanging

**Evidence:**
```yaml
# render.yaml
services:
  - type: web
    name: ppf-backend
    plan: free  # ← This causes sleeping!
```

### 2. CORS Configuration Issues
```python
# backend/src/main.py
# Wildcard matching for Vercel preview deployments may not work correctly
vercel_origins = [
    "https://ppf-monitoring.vercel.app",
    "https://ppf-monitoring-*.vercel.app",  # ← Pattern matching may fail
]
```

### 3. No Keep-Alive Mechanism
- No ping to prevent Render from sleeping
- Backend goes to sleep during low-traffic periods

---

## Solutions (Apply in order)

### Solution 1: Add Render Keep-Alive (Immediate Fix)

The backend already has a keep-alive ping in `main.py`, but let's verify it's working:

```python
# In backend/src/main.py (around line 43-70)
# This should already exist:
async def _render_keep_alive():
    """Ping the health endpoint every 10 minutes to keep Render service awake."""
    import aiohttp
    await asyncio.sleep(60)  # Wait for startup
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://ppf-backend-w0aq.onrender.com/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        logger.debug("Keep-alive ping successful")
                    else:
                        logger.warning(f"Keep-alive ping returned {resp.status}")
        except Exception as exc:
            logger.warning(f"Keep-alive ping failed: {exc}")
        await asyncio.sleep(10 * 60)  # 10 minutes
```

### Solution 2: Fix CORS for Vercel (Code Fix)

```python
# backend/src/main.py - Replace the CORS section (lines 185-214)

# ─── CORS ─────────────────────────────────────────────────────────────────────
logger.info(f"CORS Setup - Environment: {settings.ENVIRONMENT}, is_development: {settings.is_development}")

# Define allowed origins
if settings.is_development:
    logger.info("CORS: Allowing all origins [*] in development mode")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production: Explicitly list all Vercel origins
    # Note: FastAPI doesn't support wildcards in CORS origins with credentials
    cors_origins = settings.CORS_ORIGINS.copy()
    
    # Add explicit Vercel origins (wildcard doesn't work with credentials)
    vercel_origins = [
        "https://ppf-monitoring.vercel.app",
        "https://ppf-monitoring-git-master-ai-meharbnsinghs-projects.vercel.app",
        "https://ppf-monitoring-git-develop-ai-meharbnsinghs-projects.vercel.app",
        # Add any other preview deployment URLs here
    ]
    
    for origin in vercel_origins:
        if origin not in cors_origins:
            cors_origins.append(origin)
    
    logger.info(f"CORS: Using origins: {cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],  # Optional: expose custom headers
        max_age=600,  # Cache preflight for 10 minutes
    )
```

### Solution 3: Add Frontend Retry Logic

```typescript
// frontend/src/api/client.ts or wherever you configure Axios
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000, // 30 seconds (Render can take time to wake up)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add retry logic for 503/504 errors (service unavailable/gateway timeout)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    
    // Retry on 503/504 or network errors (max 3 retries)
    if ((!response || response.status === 503 || response.status === 504) && 
        config.retryCount < 3) {
      config.retryCount = config.retryCount || 0;
      config.retryCount += 1;
      
      // Wait 2 seconds before retry
      await new Promise(resolve => setTimeout(resolve, 2000));
      return apiClient(config);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Solution 4: Add External Uptime Ping (Prevents Sleeping)

Use a free service like UptimeRobot or Pingdom to ping your backend every 5-10 minutes:

**UptimeRobot Setup:**
1. Go to https://uptimerobot.com/ (free tier available)
2. Add new monitor:
   - Type: HTTP(s)
   - URL: https://ppf-backend-w0aq.onrender.com/health
   - Interval: 5 minutes (300 seconds)
3. This will keep your Render service awake!

### Solution 5: Upgrade Render Plan (Permanent Fix)

```yaml
# render.yaml
services:
  - type: web
    name: ppf-backend
    plan: standard  # ← Change from 'free' to 'standard' ($7/month)
    # ... rest of config
```

**Benefits:**
- No sleeping
- Faster response times
- Better reliability

---

## Immediate Actions Required

### 1. Apply CORS Fix (Code Change)
```bash
# Edit backend/src/main.py with the CORS fix above
git add backend/src/main.py
git commit -m "Fix CORS for Vercel wildcard origins"
git push
```

### 2. Set Up UptimeRobot (5 minutes, free)
1. Sign up at https://uptimerobot.com/
2. Add monitor for https://ppf-backend-w0aq.onrender.com/health
3. Set interval to 5 minutes
4. Done! This prevents Render from sleeping

### 3. Test Login
1. Wait 5 minutes after UptimeRobot is set up
2. Try logging in on https://ppf-monitoring.vercel.app
3. Should work consistently now

---

## Debugging Tips

If login still fails, check these in browser DevTools (F12):

### 1. Console Tab
Look for CORS errors like:
```
Access to XMLHttpRequest blocked by CORS policy
```

### 2. Network Tab
Check the login request:
- Status: Should be 200 (not 503 or CORS error)
- Time: Should be < 5 seconds (if > 30s, Render is sleeping)

### 3. Backend Logs (Render Dashboard)
1. Go to https://dashboard.render.com/
2. Select your service
3. Check Logs tab for errors during login attempts

---

## Summary

| Issue | Priority | Fix | Cost |
|-------|----------|-----|------|
| Render sleeping | HIGH | UptimeRobot ping | Free |
| CORS wildcard | MEDIUM | Code fix | Free |
| Retry logic | LOW | Frontend code | Free |
| Permanent fix | OPTIONAL | Upgrade Render | $7/month |

**Recommended immediate fix:** Set up UptimeRobot (5 minutes) + apply CORS code fix.
