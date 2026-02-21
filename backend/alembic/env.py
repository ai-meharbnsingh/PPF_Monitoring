"""
Alembic environment configuration.
Uses the synchronous database URL from settings for schema migrations.
Import all models so Alembic can detect schema changes.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# ─── Add project root to sys.path so src.* imports work ──────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Load settings ────────────────────────────────────────────────────────────
from src.config.settings import get_settings
settings = get_settings()

# ─── Import ALL models so Alembic can diff them ───────────────────────────────
from src.config.database import Base
import src.models.workshop        # noqa: F401
import src.models.user            # noqa: F401
import src.models.pit             # noqa: F401
import src.models.device          # noqa: F401
import src.models.sensor_data     # noqa: F401
import src.models.job             # noqa: F401
import src.models.alert           # noqa: F401
import src.models.subscription    # noqa: F401
import src.models.device_command  # noqa: F401
import src.models.audit_log       # noqa: F401

# ─── Alembic Config ───────────────────────────────────────────────────────────
config = context.config

# Set the DB URL from our settings (uses sync psycopg2 driver)
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL script)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
