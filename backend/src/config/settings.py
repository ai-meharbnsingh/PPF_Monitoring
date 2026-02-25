"""
Module: settings.py
Purpose:
    Loads and validates all application configuration from settings.yaml and .env files.
    Single source of truth for all config values. No hardcoded values anywhere else.

Dependencies:
    External:
        - pyyaml >= 6.0 (YAML parsing)
        - python-dotenv >= 1.0 (env loading)
        - pydantic-settings >= 2.0 (validation)
    Internal: None

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


# ─── Project root ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _load_yaml_config() -> dict:
    """Load and return the YAML configuration file."""
    config_path_env = os.getenv("CONFIG_PATH", "config/settings.yaml")
    config_path = PROJECT_ROOT / config_path_env

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}. "
            f"Expected at PROJECT_ROOT/config/settings.yaml"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError(f"Configuration file is empty: {config_path}")

    return config


# Load YAML config once at module level
_yaml_config = _load_yaml_config()


class Settings(BaseSettings):
    """
    Centralised application settings.

    Priority (highest → lowest):
    1. Environment variables from .env
    2. Values from config/settings.yaml
    3. Default values in this class
    """

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = _yaml_config["app"]["name"]
    APP_VERSION: str = _yaml_config["app"]["version"]
    ENVIRONMENT: str = _yaml_config["app"]["environment"]
    DEBUG: bool = _yaml_config["app"]["debug"]
    API_PREFIX: str = _yaml_config["app"]["api_prefix"]

    # ── Server ───────────────────────────────────────────────────────────────
    SERVER_HOST: str = _yaml_config["server"]["host"]
    SERVER_PORT: int = _yaml_config["server"]["port"]
    WORKERS: int = _yaml_config["server"]["workers"]
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: _yaml_config["server"]["cors_origins"])

    # ── Database (sensitive values from .env) ────────────────────────────────
    # Railway / cloud providers set DATABASE_URL directly; local dev uses components
    DATABASE_URL_OVERRIDE: Optional[str] = Field(default=None, alias="DATABASE_URL")
    DATABASE_USER: str = ""
    DATABASE_PASSWORD: str = ""
    DATABASE_HOST: str = _yaml_config["database"]["host"]
    DATABASE_PORT: int = _yaml_config["database"]["port"]
    DATABASE_NAME: str = _yaml_config["database"]["name"]
    DATABASE_POOL_SIZE: int = _yaml_config["database"]["pool_size"]
    DATABASE_MAX_OVERFLOW: int = _yaml_config["database"]["max_overflow"]
    DATABASE_ECHO_SQL: bool = _yaml_config["database"]["echo_sql"]

    @property
    def DATABASE_URL(self) -> str:
        """
        Async database URL.
        If DATABASE_URL env var is set (Railway), use it directly (with asyncpg driver).
        Otherwise, construct from individual components.
        """
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            # Railway gives postgresql:// — swap to asyncpg driver
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous DB URL for Alembic migrations."""
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            if url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    # ── JWT / Auth ───────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = _yaml_config["auth"]["algorithm"]
    ACCESS_TOKEN_EXPIRE_HOURS: int = _yaml_config["auth"]["access_token_expire_hours"]
    OWNER_TOKEN_EXPIRE_HOURS: int = _yaml_config["auth"]["owner_token_expire_hours"]
    CUSTOMER_TOKEN_EXPIRE_HOURS: int = _yaml_config["auth"]["customer_token_expire_hours"]
    MAX_LOGIN_ATTEMPTS: int = _yaml_config["auth"]["max_login_attempts"]
    LOCKOUT_MINUTES: int = _yaml_config["auth"]["lockout_minutes"]
    PASSWORD_MIN_LENGTH: int = _yaml_config["auth"]["password_min_length"]
    BCRYPT_ROUNDS: int = _yaml_config["security"]["bcrypt_rounds"]

    # ── MQTT ─────────────────────────────────────────────────────────────────
    MQTT_BROKER_HOST: str
    MQTT_BROKER_PORT: int = _yaml_config["mqtt"]["broker_port"]
    MQTT_USERNAME: str
    MQTT_PASSWORD: str
    MQTT_KEEPALIVE: int = _yaml_config["mqtt"]["keepalive"]
    MQTT_QOS: int = _yaml_config["mqtt"]["qos"]
    MQTT_RECONNECT_DELAY: int = _yaml_config["mqtt"]["reconnect_delay_seconds"]
    MQTT_USE_TLS: bool = False

    # ── Video (MediaMTX) ─────────────────────────────────────────────────────
    MEDIAMTX_HOST: str = _yaml_config["video"]["mediamtx_host"]
    MEDIAMTX_RTSP_PORT: int = _yaml_config["video"]["mediamtx_rtsp_port"]
    MEDIAMTX_WEBRTC_PORT: int = _yaml_config["video"]["mediamtx_webrtc_port"]
    STREAM_TOKEN_SECRET: str
    STREAM_TOKEN_EXPIRE_HOURS: int = _yaml_config["video"]["stream_token_expire_hours"]

    # ── Notifications (optional) ──────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # ── Sensor defaults ───────────────────────────────────────────────────────
    SENSOR_OFFLINE_THRESHOLD_SECONDS: int = _yaml_config["sensor"]["offline_threshold_seconds"]
    CAMERA_OFFLINE_THRESHOLD_SECONDS: int = _yaml_config["sensor"]["camera_offline_threshold_seconds"]
    SENSOR_DATA_RETENTION_DAYS: int = _yaml_config["sensor"]["data_retention_days"]

    # ── Subscription ──────────────────────────────────────────────────────────
    TRIAL_DAYS: int = _yaml_config["subscriptions"]["trial_days"]
    GRACE_PERIOD_DAYS: int = _yaml_config["subscriptions"]["grace_period_days"]

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = _yaml_config["security"]["rate_limit_per_minute"]
    RATE_LIMIT_LOGIN_PER_MINUTE: int = _yaml_config["security"]["rate_limit_login_per_minute"]

    # ── Super Admin (first-run seed) ──────────────────────────────────────────
    SUPER_ADMIN_USERNAME: str = "super_admin"
    SUPER_ADMIN_PASSWORD: str
    SUPER_ADMIN_EMAIL: str = "admin@ppf-monitor.com"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = _yaml_config["logging"]["level"]
    LOG_FILE_PATH: str = _yaml_config["logging"]["file_path"]

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from JSON string (env var) or list (YAML)."""
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's a plain string, wrap in list
                return [v]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def sms_enabled(self) -> bool:
        cfg = _yaml_config.get("features", {}).get("sms_notifications", {})
        return cfg.get("enabled", False) and bool(self.TWILIO_ACCOUNT_SID)

    @property
    def email_enabled(self) -> bool:
        cfg = _yaml_config.get("features", {}).get("email_notifications", {})
        return cfg.get("enabled", False) and bool(self.SMTP_HOST)

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached Settings instance.
    Using lru_cache ensures settings are loaded once per process lifecycle.
    """
    return Settings()
