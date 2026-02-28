#!/usr/bin/env python3
"""
Script: clear_data.py
Purpose: Clear all device data, sensor readings, jobs, etc.
         Keeps only user accounts and workshop structure.

Usage:
    # Local/Docker
    python scripts/clear_data.py
    
    # Or use the SQL file directly
    psql $DATABASE_URL -f scripts/clear_all_data_keep_users.sql

Author: PPF Monitoring Team
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ppf_user:ppf_pass@localhost:5432/ppf_db"
)

# Convert to asyncpg URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


CLEAR_TABLES = [
    # Order matters for FK constraints
    "audit_logs",
    "device_commands",
    "alerts",
    "pit_alert_configs",
    "alert_configs",
    "job_status_history",
    "jobs",
    "sensor_data",
    "subscriptions",
    "devices",
]

RESET_PITS_SQL = """
UPDATE pits SET 
    camera_ip = NULL,
    camera_rtsp_url = NULL,
    camera_model = NULL,
    camera_username = NULL,
    camera_is_online = FALSE,
    camera_last_seen = NULL,
    status = 'active'
"""

RESET_WORKSHOPS_SQL = """
UPDATE workshops SET 
    total_pits = 0,
    subscription_status = 'trial',
    subscription_expires_at = NULL,
    updated_at = NOW()
"""


async def clear_data():
    """Clear all data except users, workshops, and sensor_types."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        async with session.begin():
            print("🧹 Starting data cleanup...")
            
            # Delete from tables in order
            for table in CLEAR_TABLES:
                result = await session.execute(text(f"DELETE FROM {table}"))
                print(f"  ✓ Cleared table: {table}")
            
            # Reset pits (remove camera/device associations)
            result = await session.execute(text(RESET_PITS_SQL))
            print(f"  ✓ Reset pits (cleared camera associations)")
            
            # Reset workshops
            result = await session.execute(text(RESET_WORKSHOPS_SQL))
            print(f"  ✓ Reset workshops")
            
        # Verify counts (outside transaction)
        print("\n📊 Verification:")
        
        tables_to_check = [
            ("users", "Users remaining"),
            ("workshops", "Workshops remaining"),
            ("pits", "Pits remaining"),
            ("devices", "Devices remaining"),
            ("sensor_data", "Sensor data rows"),
            ("jobs", "Jobs remaining"),
            ("alerts", "Alerts remaining"),
        ]
        
        for table, label in tables_to_check:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {label}: {count}")
    
    await engine.dispose()
    print("\n✅ Data cleanup complete!")
    print("\nNote: Only user accounts and workshop structure preserved.")
    print("      All devices, sensor data, jobs, and alerts have been deleted.")


if __name__ == "__main__":
    # Safety confirmation
    print("=" * 60)
    print("WARNING: This will DELETE ALL DATA except user accounts!")
    print("=" * 60)
    print("\nTables that will be CLEARED:")
    for t in CLEAR_TABLES:
        print(f"  - {t}")
    print("\nTables that will be RESET:")
    print("  - pits (camera associations cleared)")
    print("  - workshops (pit counts reset)")
    print("\nTables PRESERVED:")
    print("  - users (login accounts)")
    print("  - sensor_types (reference data)")
    print("=" * 60)
    
    response = input("\nType 'DELETE' to confirm: ")
    if response != "DELETE":
        print("❌ Cancelled.")
        sys.exit(0)
    
    asyncio.run(clear_data())
