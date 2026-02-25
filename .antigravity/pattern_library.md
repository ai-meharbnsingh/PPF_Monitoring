# Pattern Library

---

## Pattern: The Pydantic JSON List Env Parsing Trap

**Date:** 2026-02-24
**Source:** PPF Monitoring `settings.py` CORS_ORIGINS field

**Trigger:** A Pydantic `BaseSettings` field is typed as `str | List[str]`. The env var is set as a comma-separated string (`CORS_ORIGINS=http://a,http://b`). A `field_validator(mode="before")` tries to split on commas. However, `pydantic-settings` v2 **pre-parses** env vars that look like JSON. If someone writes `CORS_ORIGINS=["http://a"]`, it arrives as a Python list. If they write `CORS_ORIGINS=[http://a]` (invalid JSON), it arrives as the raw string `[http://a]`.

**The Trap:** The validator checks `v.startswith("[")` to detect JSON arrays, but this branch falls through to `return v` which returns the **raw string** — not a list. `CORSMiddleware` then iterates over characters.

**Fix (Generalized Rule):**
1. Always normalize to a list explicitly. Never `return v` for a string when a list is expected.
2. If `v.startswith("[")`, try `json.loads(v)` and handle the `JSONDecodeError` with a clear error message.
3. Better pattern:
```python
@field_validator("CORS_ORIGINS", mode="before")
@classmethod
def assemble_cors_origins(cls, v):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        if v.startswith("["):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            raise ValueError(f"CORS_ORIGINS looks like a JSON array but isn't valid: {v}")
        return [i.strip() for i in v.split(",") if i.strip()]
    raise ValueError(f"CORS_ORIGINS must be a list or comma-separated string, got {type(v)}")
```

---

## Pattern: The Manual Seed Script Trap

**Date:** 2026-02-24
**Source:** PPF Monitoring `setup_db.py` + `docker-compose.yml`

**Trigger:** The system's first-run data (super_admin, migrations, seed data) depends on a **manual** `docker compose exec` command that is documented in comments but not automated. The main app's `lifespan` hook does not check if the DB is initialized.

**The Trap:** Operator runs `docker compose up -d`, sees all services green, assumes the system is ready. But no users exist, so the API returns 401 on every authenticated endpoint. There is no obvious error — the healthcheck at `/api/v1/health` may pass because it only checks if the app is running, not if the DB is seeded.

**Fix (Generalized Rule):**
1. Add a startup check in the app's lifespan that verifies critical seed data exists (e.g., at least one super_admin user).
2. OR: Wire the setup script into the Docker entrypoint with an idempotent guard (`ON CONFLICT DO NOTHING`, `if not exists` checks).
3. OR: Add a readiness endpoint (separate from liveness) that returns 503 until the DB is seeded, and configure the healthcheck to use that.

---

## Pattern: The Soft-Continue After Critical Failure

**Date:** 2026-02-24
**Source:** PPF Monitoring `setup_db.py:287-289`

**Trigger:** A multi-step setup script encounters a failure in step N but continues to step N+1. The subsequent steps depend on the artifacts of step N (e.g., tables created by migrations are needed by the seed steps).

**The Trap:** The script prints a yellow warning ("Continuing without confirmed migrations") and proceeds. If the tables genuinely don't exist, the seed functions crash with `ProgrammingError`. The operator sees a confusing stack trace instead of the clear "fix your migrations" message.

**Fix (Generalized Rule):**
1. After a critical step, verify its postconditions before continuing (e.g., `SELECT 1 FROM information_schema.tables WHERE table_name = 'users'`).
2. If the postcondition fails, **abort** — don't optimistically continue.
3. Alternatively, wrap the continuation in a try/except that catches the downstream error and maps it back to the root cause: "Seed failed because migrations didn't create the required tables."

---

## Pattern: The Placeholder Secret That Passes Validation

**Date:** 2026-02-24
**Source:** PPF Monitoring `.env` + `settings.py`

**Trigger:** A `.env` template ships with placeholder values like `JWT_SECRET_KEY=your_256_bit_secret_key_here_generate_with_secrets_module`. The app has a validator that checks `len(v) < 32`, but the placeholder is 53 chars long and passes.

**The Trap:** The app starts successfully with a **publicly known** secret. JWT tokens are signed with a value that's in the Git history / template file. Anyone with access to the repo can forge admin tokens.

**Fix (Generalized Rule):**
1. Add an entropy check (e.g., reject strings with very low Shannon entropy or that match common placeholder patterns like `your_*_here`).
2. Or use a regex denylist: `if re.match(r'.*(your|change|replace|example|placeholder).*', v, re.I): raise ValueError(...)`.
3. Or require secrets to be hex-encoded: `if not re.match(r'^[0-9a-f]{64}$', v): raise ValueError(...)`.
