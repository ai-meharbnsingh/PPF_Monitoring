"""
Script: setup_db.py
Purpose:
    Complete first-run database initialisation for PPF Workshop Monitoring System.
    Runs in order:
        1. Verify database connection
        2. Run Alembic migrations (creates all tables)
        3. Seed sensor types  (DHT22 · PMS5003 · BME680)
        4. Create super-admin account
        5. Print audit summary of what was created / already existed

Usage:
    python scripts/setup/setup_db.py

Author: PPF Monitoring Team
Created: 2026-02-22
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Add project root to sys.path ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config.settings import get_settings
from src.utils.logger import get_logger

# Import all models so SQLAlchemy relationship() references resolve correctly
import src.models.user          # noqa: F401
import src.models.workshop      # noqa: F401
import src.models.pit           # noqa: F401
import src.models.device        # noqa: F401
import src.models.sensor_data   # noqa: F401
import src.models.job           # noqa: F401
import src.models.subscription  # noqa: F401
import src.models.alert         # noqa: F401
import src.models.audit_log     # noqa: F401
import src.models.device_command  # noqa: F401

logger = get_logger("setup_db")
settings = get_settings()

# ── Colours for terminal output ───────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET}  {msg}")
def warn(msg: str) -> None: print(f"  {YELLOW}⚠{RESET}  {msg}")
def fail(msg: str) -> None: print(f"  {RED}✗{RESET}  {msg}")
def info(msg: str) -> None: print(f"  {CYAN}→{RESET}  {msg}")
def step(msg: str) -> None: print(f"\n{BOLD}{msg}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Database connection check
# ─────────────────────────────────────────────────────────────────────────────
async def check_db_connection(engine) -> bool:
    step("STEP 1 — Checking database connection")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar_one()
            ok(f"Connected to PostgreSQL: {version.split(',')[0]}")
            return True
    except Exception as exc:
        fail(f"Cannot connect to database: {exc}")
        info(f"URL: {settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")
        info("Check .env values: DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_NAME")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Alembic migrations
# ─────────────────────────────────────────────────────────────────────────────
def run_migrations() -> bool:
    step("STEP 2 — Running Alembic migrations")
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    ok(line.strip())
            ok("Migrations applied successfully")
            return True
        else:
            fail("Migration failed:")
            for line in result.stderr.strip().splitlines():
                print(f"       {line}")
            info("Tip: make sure you have run: alembic revision --autogenerate -m 'initial'")
            return False
    except FileNotFoundError:
        fail("alembic command not found — is it installed? pip install alembic")
        return False
    except Exception as exc:
        fail(f"Migration error: {exc}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Seed sensor types
# ─────────────────────────────────────────────────────────────────────────────
SENSOR_TYPES = [
    {
        "code": "DHT22",
        "name": "Capacitive Humidity & Temperature Sensor",
        "manufacturer": "AOSONG",
        "protocol": "GPIO",
        "capabilities": json.dumps({
            "temperature": True, "humidity": True,
            "pressure": False, "pm25": False, "pm10": False,
            "iaq": False, "gas_resistance": False,
        }),
        "description": (
            "Primary sensor for temperature and humidity. "
            "Single-wire protocol. Accuracy: ±0.5°C temp, ±2-5% humidity. "
            "Max read rate: 0.5 Hz."
        ),
    },
    {
        "code": "PMS5003",
        "name": "Plantower Particulate Matter Sensor",
        "manufacturer": "Plantower",
        "protocol": "UART",
        "capabilities": json.dumps({
            "temperature": False, "humidity": False,
            "pressure": False, "pm25": True, "pm10": True,
            "iaq": False, "gas_resistance": False,
        }),
        "description": (
            "Laser-based air quality sensor. "
            "Provides PM1.0, PM2.5, PM10 in μg/m³ plus particle counts by size. "
            "Used alongside DHT22 as air quality sensor."
        ),
    },
    {
        "code": "BME680",
        "name": "Bosch Environmental Sensor",
        "manufacturer": "Bosch Sensortec",
        "protocol": "I2C/SPI",
        "capabilities": json.dumps({
            "temperature": True, "humidity": True,
            "pressure": True, "pm25": False, "pm10": False,
            "iaq": True, "gas_resistance": True,
        }),
        "description": (
            "Alternative all-in-one environmental sensor. "
            "Measures temp, humidity, pressure, gas resistance, and computes IAQ index "
            "via Bosch BSEC library. Replaces DHT22+PMS5003 when used standalone."
        ),
    },
    {
        "code": "BME688",
        "name": "Bosch BME688 Environmental Sensor",
        "manufacturer": "Bosch Sensortec",
        "protocol": "I2C/SPI",
        "capabilities": json.dumps({
            "temperature": True, "humidity": True,
            "pressure": True, "pm25": False, "pm10": False,
            "iaq": True, "gas_resistance": True,
        }),
        "description": (
            "Next-gen all-in-one environmental sensor (pin-compatible with BME680). "
            "Measures temp, humidity, pressure, gas resistance, and computes IAQ index. "
            "Primary sensor for BME688+DHT fallback configuration."
        ),
    },
    {
        "code": "DHT11",
        "name": "Basic Temperature & Humidity Sensor",
        "manufacturer": "AOSONG",
        "protocol": "GPIO",
        "capabilities": json.dumps({
            "temperature": True, "humidity": True,
            "pressure": False, "pm25": False, "pm10": False,
            "iaq": False, "gas_resistance": False,
        }),
        "description": (
            "Basic digital temperature and humidity sensor. "
            "Single-wire protocol. Accuracy: ±2°C temp, ±5% humidity. "
            "Used as fallback sensor when BME688 is unavailable."
        ),
    },
]


async def seed_sensor_types(session: AsyncSession) -> dict:
    step("STEP 3 — Seeding sensor types (DHT22 · PMS5003 · BME680 · BME688 · DHT11)")
    from src.models.device import SensorType

    stats = {"created": 0, "exists": 0}
    for st_data in SENSOR_TYPES:
        result = await session.execute(
            select(SensorType).where(SensorType.code == st_data["code"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            warn(f"Sensor type already exists: {st_data['code']} (id={existing.id}) — skipping")
            stats["exists"] += 1
        else:
            st = SensorType(
                code=st_data["code"],
                name=st_data["name"],
                manufacturer=st_data["manufacturer"],
                protocol=st_data["protocol"],
                capabilities=st_data["capabilities"],
                description=st_data["description"],
                is_active=True,
            )
            session.add(st)
            await session.flush()
            ok(f"Sensor type created: {st_data['code']} (id={st.id})")
            stats["created"] += 1

    await session.commit()
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Create super admin
# ─────────────────────────────────────────────────────────────────────────────
async def seed_super_admin(session: AsyncSession) -> dict:
    step("STEP 4 — Creating super admin account")
    from src.models.user import User
    from src.services.auth_service import hash_password
    from src.utils.constants import UserRole

    result = await session.execute(
        select(User).where(User.username == settings.SUPER_ADMIN_USERNAME)
    )
    existing = result.scalar_one_or_none()

    if existing:
        warn(
            f"Super admin already exists: '{settings.SUPER_ADMIN_USERNAME}' "
            f"(id={existing.id}) — skipping"
        )
        return {"action": "skipped", "user_id": existing.id}

    admin = User(
        username=settings.SUPER_ADMIN_USERNAME,
        email=settings.SUPER_ADMIN_EMAIL,
        password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
        role=UserRole.SUPER_ADMIN.value,
        is_active=True,
        is_temporary_password=False,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    ok(f"Super admin created: '{admin.username}' (id={admin.id})")
    info(f"Email:    {settings.SUPER_ADMIN_EMAIL}")
    info(f"Password: (set in .env → SUPER_ADMIN_PASSWORD)")
    return {"action": "created", "user_id": admin.id}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Audit summary
# ─────────────────────────────────────────────────────────────────────────────
async def print_audit_summary(session: AsyncSession) -> None:
    step("STEP 5 — Audit summary")

    from src.models.device import SensorType, Device
    from src.models.user import User
    from src.models.workshop import Workshop
    from src.models.pit import Pit
    from src.models.subscription import Subscription
    from sqlalchemy import func

    rows = {
        "Sensor types":  (await session.execute(select(func.count(SensorType.id)))).scalar_one(),
        "Users":         (await session.execute(select(func.count(User.id)))).scalar_one(),
        "Workshops":     (await session.execute(select(func.count(Workshop.id)))).scalar_one(),
        "Pits":          (await session.execute(select(func.count(Pit.id)))).scalar_one(),
        "Devices":       (await session.execute(select(func.count(Device.id)))).scalar_one(),
        "Subscriptions": (await session.execute(select(func.count(Subscription.id)))).scalar_one(),
    }

    print()
    print(f"  {'Table':<20} {'Row count':>10}")
    print(f"  {'─'*20} {'─'*10}")
    for table, count in rows.items():
        status = GREEN if count > 0 else YELLOW
        print(f"  {table:<20} {status}{count:>10}{RESET}")

    print()
    info(f"Database:    {settings.DATABASE_NAME}  ({settings.DATABASE_HOST}:{settings.DATABASE_PORT})")
    info(f"Environment: {settings.ENVIRONMENT}")
    info(f"App:         {settings.APP_NAME} v{settings.APP_VERSION}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
async def main() -> None:
    print()
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  PPF Workshop Monitoring System — Database Setup{RESET}")
    print(f"  {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{BOLD}{'═'*60}{RESET}")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # ── Step 1: DB connection ────────────────────────────────────────────────
    connected = await check_db_connection(engine)
    if not connected:
        print(f"\n{RED}Setup aborted — fix database connection first.{RESET}\n")
        await engine.dispose()
        sys.exit(1)

    # ── Step 2: Migrations ───────────────────────────────────────────────────
    migration_ok = run_migrations()
    if not migration_ok:
        print(f"\n{YELLOW}Continuing without confirmed migrations (tables may already exist).{RESET}")

    async with SessionLocal() as session:
        # ── Step 3: Sensor types ─────────────────────────────────────────────
        sensor_stats = await seed_sensor_types(session)

        # ── Step 4: Super admin ───────────────────────────────────────────────
        admin_result = await seed_super_admin(session)

        # ── Step 5: Audit summary ─────────────────────────────────────────────
        await print_audit_summary(session)

    await engine.dispose()

    print()
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"{GREEN}{BOLD}  Setup complete!{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print()
    print("  Next steps:")
    print("  1. Start the server:")
    print(f"     uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("  2. Open API docs:")
    print(f"     http://localhost:8000/docs")
    print()
    print("  3. Login as super admin:")
    print(f"     POST /api/v1/auth/login")
    print(f"     Username: {settings.SUPER_ADMIN_USERNAME}")
    print(f"     Password: <your SUPER_ADMIN_PASSWORD from .env>")
    print()


if __name__ == "__main__":
    asyncio.run(main())
