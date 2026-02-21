"""
Script: audit_report.py
Purpose:
    Generate a full operational audit report for a running PPF system.
    Covers: subscriptions health, device status, active jobs, recent alerts,
    audit log activity, and system health indicators.

Usage:
    python scripts/maintenance/audit_report.py
    python scripts/maintenance/audit_report.py --workshop-id 3
    python scripts/maintenance/audit_report.py --export audit_report.txt

Author: PPF Monitoring Team
Created: 2026-02-22
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ── Add project root ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config.settings import get_settings

settings = get_settings()

# ── Terminal colours ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

_output_lines: list[str] = []


def _print(line: str = "") -> None:
    print(line)
    _output_lines.append(line)


def section(title: str) -> None:
    _print()
    _print(f"{BOLD}{'─'*60}{RESET}")
    _print(f"{BOLD}  {title}{RESET}")
    _print(f"{BOLD}{'─'*60}{RESET}")


def row(label: str, value, warn_if_zero: bool = False, good_if_zero: bool = False) -> None:
    val_str = str(value)
    if isinstance(value, int):
        if warn_if_zero and value == 0:
            color = YELLOW
        elif good_if_zero and value == 0:
            color = GREEN
        elif isinstance(value, int) and value > 0:
            color = GREEN
        else:
            color = RESET
    else:
        color = RESET
    _print(f"  {label:<40} {color}{val_str}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
async def run_audit(session: AsyncSession, workshop_id: Optional[int]) -> None:
    from src.models.workshop import Workshop
    from src.models.user import User
    from src.models.pit import Pit
    from src.models.device import Device
    from src.models.subscription import Subscription
    from src.models.job import Job
    from src.models.alert import Alert
    from src.models.audit_log import AuditLog
    from src.models.sensor_data import SensorData
    from src.utils.constants import (
        JobStatus, DeviceStatus, SubscriptionStatus, AlertSeverity
    )

    now = datetime.now(tz=timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7d  = now - timedelta(days=7)

    # ── Workshop filter ───────────────────────────────────────────────────────
    ws_filter = []
    if workshop_id:
        ws_filter = [Workshop.id == workshop_id]

    # ── Header ────────────────────────────────────────────────────────────────
    _print()
    _print(f"{BOLD}{'═'*60}{RESET}")
    _print(f"{BOLD}  PPF Workshop Monitoring System — Audit Report{RESET}")
    _print(f"  Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if workshop_id:
        _print(f"  Scope:     Workshop ID = {workshop_id}")
    else:
        _print(f"  Scope:     All workshops (system-wide)")
    _print(f"{BOLD}{'═'*60}{RESET}")

    # ── SECTION 1: Workshops ──────────────────────────────────────────────────
    section("1. WORKSHOPS")
    q = select(func.count(Workshop.id))
    if ws_filter:
        q = q.where(*ws_filter)
    total_ws = (await session.execute(q)).scalar_one()

    active_ws = (await session.execute(
        select(func.count(Workshop.id)).where(Workshop.is_active.is_(True), *ws_filter)
    )).scalar_one()

    trial_ws = (await session.execute(
        select(func.count(Workshop.id)).where(
            Workshop.subscription_status == "trial", *ws_filter
        )
    )).scalar_one()

    suspended_ws = (await session.execute(
        select(func.count(Workshop.id)).where(
            Workshop.subscription_status.in_(["suspended", "expired"]), *ws_filter
        )
    )).scalar_one()

    row("Total workshops",                total_ws, warn_if_zero=True)
    row("  Active",                       active_ws)
    row("  On trial",                     trial_ws)
    row("  Suspended / Expired",          suspended_ws,
        warn_if_zero=False if suspended_ws == 0 else True)

    # List suspended workshops
    if suspended_ws > 0:
        _print()
        _print(f"  {YELLOW}Suspended/Expired workshops:{RESET}")
        ws_list = await session.execute(
            select(Workshop).where(
                Workshop.subscription_status.in_(["suspended", "expired"]), *ws_filter
            )
        )
        for ws in ws_list.scalars():
            exp = ws.subscription_expires_at.strftime("%Y-%m-%d") if ws.subscription_expires_at else "N/A"
            _print(f"    id={ws.id}  name='{ws.name}'  status={ws.subscription_status}  expires={exp}")

    # ── SECTION 2: Subscriptions ──────────────────────────────────────────────
    section("2. SUBSCRIPTIONS & LICENSES")
    sub_q_base = select(Subscription)
    if workshop_id:
        sub_q_base = sub_q_base.where(Subscription.workshop_id == workshop_id)

    total_subs = (await session.execute(
        select(func.count()).select_from(sub_q_base.subquery())
    )).scalar_one()

    active_subs = (await session.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status == SubscriptionStatus.ACTIVE.value,
            *([Subscription.workshop_id == workshop_id] if workshop_id else [])
        )
    )).scalar_one()

    expired_subs = (await session.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status == SubscriptionStatus.EXPIRED.value,
            *([Subscription.workshop_id == workshop_id] if workshop_id else [])
        )
    )).scalar_one()

    # Expiring in next 7 days
    expiring_soon = (await session.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status == SubscriptionStatus.ACTIVE.value,
            Subscription.expires_at.isnot(None),
            Subscription.expires_at <= now + timedelta(days=7),
            Subscription.expires_at >= now,
            *([Subscription.workshop_id == workshop_id] if workshop_id else [])
        )
    )).scalar_one()

    row("Total subscriptions",            total_subs, warn_if_zero=True)
    row("  Active",                       active_subs)
    row("  Expired",                      expired_subs,
        warn_if_zero=False if expired_subs == 0 else True)

    if expiring_soon > 0:
        _print(f"\n  {YELLOW}⚠  {expiring_soon} subscription(s) expiring within 7 days:{RESET}")
        exp_list = await session.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.ACTIVE.value,
                Subscription.expires_at.isnot(None),
                Subscription.expires_at <= now + timedelta(days=7),
                Subscription.expires_at >= now,
                *([Subscription.workshop_id == workshop_id] if workshop_id else [])
            )
        )
        for sub in exp_list.scalars():
            days_left = (sub.expires_at - now).days
            _print(
                f"    sub_id={sub.id}  device='{sub.device_id}'  "
                f"plan={sub.plan}  expires={sub.expires_at.strftime('%Y-%m-%d')}  "
                f"({days_left}d left)"
            )
    else:
        row("  Expiring within 7 days",   expiring_soon, good_if_zero=True)

    # ── SECTION 3: Devices ────────────────────────────────────────────────────
    section("3. DEVICES")
    dev_base = select(Device)
    if workshop_id:
        dev_base = dev_base.where(Device.workshop_id == workshop_id)

    total_dev  = (await session.execute(select(func.count()).select_from(dev_base.subquery()))).scalar_one()
    online_dev = (await session.execute(
        select(func.count(Device.id)).where(
            Device.is_online.is_(True),
            *([Device.workshop_id == workshop_id] if workshop_id else [])
        )
    )).scalar_one()
    disabled_dev = (await session.execute(
        select(func.count(Device.id)).where(
            Device.status == DeviceStatus.DISABLED.value,
            *([Device.workshop_id == workshop_id] if workshop_id else [])
        )
    )).scalar_one()
    # Devices not seen in 2× offline threshold (stale)
    stale_threshold = now - timedelta(seconds=settings.SENSOR_OFFLINE_THRESHOLD_SECONDS * 2)
    stale_dev = (await session.execute(
        select(func.count(Device.id)).where(
            Device.last_seen < stale_threshold,
            Device.status == DeviceStatus.ACTIVE.value,
            *([Device.workshop_id == workshop_id] if workshop_id else [])
        )
    )).scalar_one()

    row("Total devices",                  total_dev, warn_if_zero=True)
    row("  Online",                       online_dev)
    row("  Offline / Not seen",           total_dev - online_dev)
    row("  Disabled",                     disabled_dev)
    row("  Stale (no data >2× threshold)",stale_dev,
        warn_if_zero=False if stale_dev == 0 else True)

    # List disabled devices
    if disabled_dev > 0:
        _print(f"\n  {RED}✗  Disabled devices:{RESET}")
        dis_list = await session.execute(
            select(Device).where(
                Device.status == DeviceStatus.DISABLED.value,
                *([Device.workshop_id == workshop_id] if workshop_id else [])
            )
        )
        for d in dis_list.scalars():
            _print(f"    device_id='{d.device_id}'  workshop_id={d.workshop_id}  last_seen={d.last_seen}")

    # ── SECTION 4: Jobs ───────────────────────────────────────────────────────
    section("4. JOBS")
    job_base_filter = [Job.workshop_id == workshop_id] if workshop_id else []

    total_jobs   = (await session.execute(select(func.count(Job.id)).where(*job_base_filter))).scalar_one()
    waiting      = (await session.execute(select(func.count(Job.id)).where(Job.status == JobStatus.WAITING.value, *job_base_filter))).scalar_one()
    in_progress  = (await session.execute(select(func.count(Job.id)).where(Job.status == JobStatus.IN_PROGRESS.value, *job_base_filter))).scalar_one()
    qc_jobs      = (await session.execute(select(func.count(Job.id)).where(Job.status == JobStatus.QUALITY_CHECK.value, *job_base_filter))).scalar_one()
    completed_7d = (await session.execute(
        select(func.count(Job.id)).where(
            Job.status == JobStatus.COMPLETED.value,
            Job.actual_end_time >= last_7d,
            *job_base_filter
        )
    )).scalar_one()
    cancelled_7d = (await session.execute(
        select(func.count(Job.id)).where(
            Job.status == JobStatus.CANCELLED.value,
            Job.updated_at >= last_7d,
            *job_base_filter
        )
    )).scalar_one()

    row("Total jobs (all time)",          total_jobs)
    row("  Currently waiting",            waiting)
    row("  In progress",                  in_progress)
    row("  Quality check",                qc_jobs)
    row("  Completed (last 7 days)",      completed_7d)
    row("  Cancelled (last 7 days)",      cancelled_7d)

    # ── SECTION 5: Sensor Data ────────────────────────────────────────────────
    section("5. SENSOR DATA (LAST 24 HOURS)")
    sensor_base_filter = [SensorData.created_at >= last_24h]
    if workshop_id:
        sensor_base_filter.append(SensorData.workshop_id == workshop_id)

    total_readings = (await session.execute(
        select(func.count(SensorData.id)).where(*sensor_base_filter)
    )).scalar_one()
    invalid_readings = (await session.execute(
        select(func.count(SensorData.id)).where(
            SensorData.is_valid.is_(False), *sensor_base_filter
        )
    )).scalar_one()

    # Pits that sent NO data in last 24h (potential offline)
    pits_with_data = (await session.execute(
        select(func.count(func.distinct(SensorData.pit_id))).where(*sensor_base_filter)
    )).scalar_one()

    row("Readings in last 24h",           total_readings, warn_if_zero=True)
    row("  Invalid readings",             invalid_readings,
        warn_if_zero=False if invalid_readings == 0 else True)
    row("  Unique pits reporting data",   pits_with_data)

    # ── SECTION 6: Alerts ─────────────────────────────────────────────────────
    section("6. ALERTS")
    alert_base_filter = []
    if workshop_id:
        alert_base_filter = [Alert.workshop_id == workshop_id]

    total_alerts_24h  = (await session.execute(
        select(func.count(Alert.id)).where(Alert.created_at >= last_24h, *alert_base_filter)
    )).scalar_one()
    unacked_alerts     = (await session.execute(
        select(func.count(Alert.id)).where(Alert.is_acknowledged.is_(False), *alert_base_filter)
    )).scalar_one()
    critical_unacked   = (await session.execute(
        select(func.count(Alert.id)).where(
            Alert.is_acknowledged.is_(False),
            Alert.severity == AlertSeverity.CRITICAL.value,
            *alert_base_filter
        )
    )).scalar_one()

    row("Alerts in last 24h",             total_alerts_24h)
    row("  Unacknowledged (all time)",    unacked_alerts,
        warn_if_zero=False if unacked_alerts == 0 else True)

    if critical_unacked > 0:
        _print(f"\n  {RED}⚠  {critical_unacked} CRITICAL unacknowledged alert(s):{RESET}")
        crit_list = await session.execute(
            select(Alert).where(
                Alert.is_acknowledged.is_(False),
                Alert.severity == AlertSeverity.CRITICAL.value,
                *alert_base_filter
            ).order_by(Alert.created_at.desc()).limit(10)
        )
        for a in crit_list.scalars():
            _print(
                f"    id={a.id}  pit_id={a.pit_id}  type={a.alert_type}  "
                f"msg='{a.message[:60]}'  at={a.created_at.strftime('%m-%d %H:%M')}"
            )
    else:
        row("  Critical unacknowledged",  critical_unacked, good_if_zero=True)

    # ── SECTION 7: Audit Logs ─────────────────────────────────────────────────
    section("7. AUDIT LOG ACTIVITY (LAST 24 HOURS)")
    from src.models.audit_log import AuditLog

    audit_filter = [AuditLog.created_at >= last_24h]
    if workshop_id:
        audit_filter.append(AuditLog.workshop_id == workshop_id)

    total_audit = (await session.execute(
        select(func.count(AuditLog.id)).where(*audit_filter)
    )).scalar_one()

    # Action breakdown
    action_counts = await session.execute(
        select(
            func.split_part(AuditLog.action, ".", 1).label("category"),
            func.count(AuditLog.id).label("count")
        ).where(*audit_filter)
        .group_by("category")
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
    )

    row("Total audit entries (24h)",      total_audit)
    if total_audit > 0:
        _print()
        _print(f"  {'Action category':<30} {'Count':>8}")
        _print(f"  {'─'*30} {'─'*8}")
        for cat, count in action_counts:
            _print(f"  {(cat or 'unknown'):<30} {count:>8}")

    # ── SECTION 8: Users ──────────────────────────────────────────────────────
    section("8. USERS")
    from src.utils.constants import UserRole

    user_filter = []
    if workshop_id:
        user_filter = [User.workshop_id == workshop_id]

    for role in [UserRole.OWNER, UserRole.STAFF, UserRole.CUSTOMER]:
        count = (await session.execute(
            select(func.count(User.id)).where(User.role == role.value, *user_filter)
        )).scalar_one()
        row(f"  {role.value.capitalize()} accounts", count)

    inactive_users = (await session.execute(
        select(func.count(User.id)).where(User.is_active.is_(False), *user_filter)
    )).scalar_one()
    temp_pass_users = (await session.execute(
        select(func.count(User.id)).where(User.is_temporary_password.is_(True), *user_filter)
    )).scalar_one()

    row("  Inactive accounts",            inactive_users)
    row("  Using temporary passwords",    temp_pass_users,
        warn_if_zero=False if temp_pass_users == 0 else True)

    # ── Footer ────────────────────────────────────────────────────────────────
    _print()
    _print(f"{BOLD}{'═'*60}{RESET}")
    _print(f"{GREEN}{BOLD}  Report complete.{RESET}")
    _print(f"  Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    _print(f"{BOLD}{'═'*60}{RESET}")
    _print()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
async def main(workshop_id: Optional[int], export_path: Optional[str]) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with SessionLocal() as session:
            await run_audit(session, workshop_id)
    except Exception as exc:
        print(f"\n{RED}Audit failed: {exc}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

    # Export to file if requested
    if export_path:
        # Strip ANSI codes for file output
        import re
        ansi_escape = re.compile(r"\033\[[0-9;]*m")
        clean_lines = [ansi_escape.sub("", line) for line in _output_lines]
        Path(export_path).write_text("\n".join(clean_lines), encoding="utf-8")
        print(f"\n  Report saved to: {export_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PPF Workshop Monitoring System — Operational Audit Report"
    )
    parser.add_argument(
        "--workshop-id",
        type=int,
        default=None,
        help="Scope report to a single workshop ID (default: all workshops)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        metavar="FILE",
        help="Export plain-text report to a file (e.g. audit_report.txt)",
    )
    args = parser.parse_args()
    asyncio.run(main(workshop_id=args.workshop_id, export_path=args.export))
