"""Initial schema — all tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-02-22 00:00:00.000000

Creates the complete PPF Workshop Monitoring System database schema.

Table creation order (respects FK dependency graph):
  1. sensor_types         — no FK deps
  2. users                — workshop_id FK deferred (circular)
  3. workshops            — owner_user_id FK deferred (circular)
  4. pits                 — → workshops
  5. devices              — → workshops, pits, sensor_types
  6. subscriptions        — → workshops, devices
  7. sensor_data          — → devices, pits, workshops
  8. jobs + job_status_history  — → workshops, pits, users
  9. alerts               — → workshops, pits, devices, users
 10. alert_configs        — → workshops
 11. device_commands      — → devices, workshops, users
 12. audit_logs           — → workshops, users

  Circular FK resolution (after all tables exist):
    users.workshop_id        → workshops.id
    workshops.owner_user_id  → users.id

Author: PPF Monitoring Team
"""

from alembic import op
import sqlalchemy as sa

# ─── Revision identifiers ────────────────────────────────────────────────────
revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────────
    # 1. sensor_types
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "sensor_types",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("manufacturer", sa.String(50), nullable=True),
        sa.Column("protocol", sa.String(20), nullable=True),
        sa.Column("capabilities", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 2. users — workshop_id column created WITHOUT FK (added after workshops)
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), nullable=True),   # FK added below
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("email", sa.String(100), unique=True, nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("first_name", sa.String(50), nullable=True),
        sa.Column("last_name", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_temporary_password", sa.Boolean(), default=False, nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_attempt_count", sa.Integer(), default=0, nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    # ─────────────────────────────────────────────────────────────────────────
    # 3. workshops — owner_user_id WITHOUT FK (added below after both tables exist)
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "workshops",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),   # FK added below
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(50), nullable=True),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("total_pits", sa.Integer(), default=0, nullable=False),
        sa.Column("subscription_plan", sa.String(20), default="trial", nullable=False),
        sa.Column("subscription_status", sa.String(20), default="trial", nullable=False),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(50), default="Asia/Kolkata", nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workshops_slug", "workshops", ["slug"], unique=True)
    op.create_index("ix_workshops_is_active", "workshops", ["is_active"])

    # ── Resolve the users ↔ workshops circular FK ─────────────────────────
    op.create_foreign_key(
        "fk_user_workshop_id",
        "users", "workshops",
        ["workshop_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_workshop_owner_user_id",
        "workshops", "users",
        ["owner_user_id"], ["id"],
        ondelete="SET NULL",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 4. pits
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "pits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pit_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="active", nullable=False),
        sa.Column("camera_ip", sa.String(50), nullable=True),
        sa.Column("camera_rtsp_url", sa.Text(), nullable=True),
        sa.Column("camera_model", sa.String(100), nullable=True),
        sa.Column("camera_username", sa.String(50), nullable=True),
        sa.Column("camera_is_online", sa.Boolean(), default=False, nullable=False),
        sa.Column("camera_last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("workshop_id", "pit_number", name="uq_pit_workshop_number"),
    )
    op.create_index("ix_pits_workshop_id", "pits", ["workshop_id"])

    # ─────────────────────────────────────────────────────────────────────────
    # 5. devices
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("pit_id", sa.Integer(), sa.ForeignKey("pits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(50), unique=True, nullable=False),
        sa.Column("license_key", sa.String(30), unique=True, nullable=False),
        sa.Column("firmware_version", sa.String(20), nullable=True),
        sa.Column("primary_sensor_type_id", sa.Integer(), sa.ForeignKey("sensor_types.id"), nullable=True),
        sa.Column("air_quality_sensor_type_id", sa.Integer(), sa.ForeignKey("sensor_types.id"), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        sa.Column("status", sa.String(20), default="active", nullable=False),
        sa.Column("is_online", sa.Boolean(), default=False, nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_mqtt_message", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_interval_seconds", sa.Integer(), default=10, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=True)
    op.create_index("ix_devices_workshop_id", "devices", ["workshop_id"])
    op.create_index("ix_devices_status", "devices", ["status"])

    # ─────────────────────────────────────────────────────────────────────────
    # 6. subscriptions
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(50), sa.ForeignKey("devices.device_id"), nullable=True),
        sa.Column("license_key", sa.String(30), unique=True, nullable=False),
        sa.Column("plan", sa.String(20), default="basic", nullable=False),
        sa.Column("status", sa.String(20), default="active", nullable=False),
        sa.Column("monthly_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), default="INR", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_days", sa.Integer(), default=7, nullable=False),
        sa.Column("last_payment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_payment_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_subscriptions_device_id", "subscriptions", ["device_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_expires_at", "subscriptions", ["expires_at"])

    # ─────────────────────────────────────────────────────────────────────────
    # 7. sensor_data  (high-volume time-series — index on created_at)
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "sensor_data",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(50), sa.ForeignKey("devices.device_id"), nullable=False),
        sa.Column("pit_id", sa.Integer(), sa.ForeignKey("pits.id"), nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("primary_sensor_type", sa.String(10), nullable=True),
        sa.Column("air_quality_sensor_type", sa.String(10), nullable=True),
        # DHT22 / BME680 shared
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        # BME680 only
        sa.Column("pressure", sa.Float(), nullable=True),
        sa.Column("gas_resistance", sa.Float(), nullable=True),
        sa.Column("iaq", sa.Float(), nullable=True),
        sa.Column("iaq_accuracy", sa.Integer(), nullable=True),
        # PMS5003 only
        sa.Column("pm1", sa.Float(), nullable=True),
        sa.Column("pm25", sa.Float(), nullable=True),
        sa.Column("pm10", sa.Float(), nullable=True),
        sa.Column("particles_03um", sa.Integer(), nullable=True),
        sa.Column("particles_05um", sa.Integer(), nullable=True),
        sa.Column("particles_10um", sa.Integer(), nullable=True),
        sa.Column("particles_25um", sa.Integer(), nullable=True),
        sa.Column("particles_50um", sa.Integer(), nullable=True),
        sa.Column("particles_100um", sa.Integer(), nullable=True),
        # Data quality
        sa.Column("is_valid", sa.Boolean(), default=True, nullable=False),
        sa.Column("validation_notes", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("device_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sensor_data_pit_created", "sensor_data", ["pit_id", "created_at"])
    op.create_index("ix_sensor_data_workshop_created", "sensor_data", ["workshop_id", "created_at"])
    op.create_index("ix_sensor_data_device_created", "sensor_data", ["device_id", "created_at"])
    op.create_index("ix_sensor_data_created_at", "sensor_data", ["created_at"])

    # ─────────────────────────────────────────────────────────────────────────
    # 8. jobs
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pit_id", sa.Integer(), sa.ForeignKey("pits.id"), nullable=False),
        sa.Column("customer_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("car_model", sa.String(100), nullable=True),
        sa.Column("car_plate", sa.String(20), nullable=True),
        sa.Column("car_color", sa.String(30), nullable=True),
        sa.Column("car_year", sa.Integer(), nullable=True),
        sa.Column("work_type", sa.String(50), nullable=False),
        sa.Column("work_description", sa.Text(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), default="waiting", nullable=False),
        sa.Column("scheduled_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_staff_ids", sa.Text(), nullable=True),   # JSON array string
        sa.Column("customer_view_token", sa.String(100), unique=True, nullable=True),
        sa.Column("customer_view_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_notes", sa.Text(), nullable=True),
        sa.Column("staff_notes", sa.Text(), nullable=True),
        sa.Column("quoted_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), default="INR", nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_workshop_status", "jobs", ["workshop_id", "status"])
    op.create_index("ix_jobs_pit_id", "jobs", ["pit_id"])
    op.create_index("ix_jobs_customer_token", "jobs", ["customer_view_token"], unique=True)
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])

    # 8b. job_status_history
    op.create_table(
        "job_status_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_status", sa.String(30), nullable=True),
        sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_history_job_id", "job_status_history", ["job_id"])

    # ─────────────────────────────────────────────────────────────────────────
    # 9. alerts
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pit_id", sa.Integer(), sa.ForeignKey("pits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("device_id", sa.String(50), sa.ForeignKey("devices.device_id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("trigger_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), default=False, nullable=False),
        sa.Column("acknowledged_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sms_sent", sa.Boolean(), default=False, nullable=False),
        sa.Column("email_sent", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_workshop_ack", "alerts", ["workshop_id", "is_acknowledged"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    # ─────────────────────────────────────────────────────────────────────────
    # 10. alert_configs
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "alert_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("temp_min", sa.Float(), default=15.0, nullable=False),
        sa.Column("temp_max", sa.Float(), default=35.0, nullable=False),
        sa.Column("humidity_max", sa.Float(), default=70.0, nullable=False),
        sa.Column("pm25_warning", sa.Float(), default=12.0, nullable=False),
        sa.Column("pm25_critical", sa.Float(), default=35.4, nullable=False),
        sa.Column("pm10_warning", sa.Float(), default=54.0, nullable=False),
        sa.Column("pm10_critical", sa.Float(), default=154.0, nullable=False),
        sa.Column("iaq_warning", sa.Float(), default=100.0, nullable=False),
        sa.Column("iaq_critical", sa.Float(), default=150.0, nullable=False),
        sa.Column("device_offline_threshold_seconds", sa.Integer(), default=60, nullable=False),
        sa.Column("camera_offline_threshold_seconds", sa.Integer(), default=30, nullable=False),
        sa.Column("notify_via_sms", sa.Boolean(), default=True, nullable=False),
        sa.Column("notify_via_email", sa.Boolean(), default=False, nullable=False),
        sa.Column("notify_via_webhook", sa.Boolean(), default=False, nullable=False),
        sa.Column("webhook_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 11. device_commands
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "device_commands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(50), sa.ForeignKey("devices.device_id"), nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("command", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),   # JSON string
        sa.Column("status", sa.String(20), default="pending", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_device_commands_device_id", "device_commands", ["device_id"])
    op.create_index("ix_device_commands_status", "device_commands", ["status"])

    # ─────────────────────────────────────────────────────────────────────────
    # 12. audit_logs  (append-only, BigInteger PK for high volume)
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workshop_id", sa.Integer(), sa.ForeignKey("workshops.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("old_data", sa.Text(), nullable=True),
        sa.Column("new_data", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_workshop_id", "audit_logs", ["workshop_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("audit_logs")
    op.drop_table("device_commands")
    op.drop_table("alert_configs")
    op.drop_table("alerts")
    op.drop_table("job_status_history")
    op.drop_table("jobs")
    op.drop_table("sensor_data")
    op.drop_table("subscriptions")
    op.drop_table("devices")
    op.drop_table("pits")

    # Drop circular FKs before dropping the linked tables
    op.drop_constraint("fk_workshop_owner_user_id", "workshops", type_="foreignkey")
    op.drop_constraint("fk_user_workshop_id", "users", type_="foreignkey")

    op.drop_table("workshops")
    op.drop_table("users")
    op.drop_table("sensor_types")
