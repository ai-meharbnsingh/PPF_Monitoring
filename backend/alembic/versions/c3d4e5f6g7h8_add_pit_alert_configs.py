"""Add pit_alert_configs table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-26 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "c3d4e5f6g7h8"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pit_alert_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pit_id", sa.Integer(), sa.ForeignKey("pits.id"), unique=True, nullable=False),
        # Temperature thresholds (°C)
        sa.Column("temp_min", sa.Float(), nullable=True),
        sa.Column("temp_max", sa.Float(), nullable=True),
        # Humidity threshold (%)
        sa.Column("humidity_max", sa.Float(), nullable=True),
        # PM2.5 thresholds (μg/m³)
        sa.Column("pm25_warning", sa.Float(), nullable=True),
        sa.Column("pm25_critical", sa.Float(), nullable=True),
        # PM10 thresholds (μg/m³)
        sa.Column("pm10_warning", sa.Float(), nullable=True),
        sa.Column("pm10_critical", sa.Float(), nullable=True),
        # BME680 IAQ thresholds
        sa.Column("iaq_warning", sa.Float(), nullable=True),
        sa.Column("iaq_critical", sa.Float(), nullable=True),
        # Offline detection (seconds)
        sa.Column("device_offline_threshold_seconds", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("pit_alert_configs")
