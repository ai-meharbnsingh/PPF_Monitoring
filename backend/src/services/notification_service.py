"""
Module: notification_service.py
Purpose:
    Send SMS and (future) email notifications for alerts.
    Twilio integration for SMS — disabled by default, enabled via settings.yaml.
    Email is stubbed — enable aiosmtplib when needed.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

from typing import Optional

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()


# ─── SMS via Twilio ───────────────────────────────────────────────────────────
async def send_sms_alert(
    to_phone: str,
    message: str,
    workshop_name: str = "",
) -> bool:
    """
    Send an SMS alert via Twilio.
    Returns True on success, False on failure.
    Never raises — notification failures must not crash the sensor pipeline.
    """
    if not _settings.sms_enabled:
        logger.debug(
            f"SMS disabled (settings). Would have sent to {to_phone}: {message[:60]}"
        )
        return False

    try:
        from twilio.rest import Client  # lazy import — optional dependency

        client = Client(
            _settings.TWILIO_ACCOUNT_SID,
            _settings.TWILIO_AUTH_TOKEN,
        )
        body = f"[{workshop_name}] {message}" if workshop_name else message
        client.messages.create(
            body=body,
            from_=_settings.TWILIO_FROM_NUMBER,
            to=to_phone,
        )
        logger.info(f"SMS sent to {to_phone}: {message[:80]}")
        return True

    except Exception as exc:
        logger.error(f"SMS send failed to {to_phone}: {exc}")
        return False


# ─── Email (stubbed — Phase 2) ─────────────────────────────────────────────────
async def send_email_alert(
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """
    Send an email alert.
    Currently a no-op stub. Uncomment aiosmtplib block when SMTP is configured.
    """
    if not _settings.email_enabled:
        logger.debug(
            f"Email disabled (settings). Would have sent to {to_email}: {subject}"
        )
        return False

    # TODO: Implement via aiosmtplib when email_notifications feature is enabled.
    # import aiosmtplib
    # from email.message import EmailMessage
    # msg = EmailMessage()
    # msg["From"] = _settings.SMTP_FROM_EMAIL
    # msg["To"] = to_email
    # msg["Subject"] = subject
    # msg.set_content(body)
    # await aiosmtplib.send(msg, hostname=_settings.SMTP_HOST, port=_settings.SMTP_PORT, ...)
    logger.warning(f"Email send not yet implemented. target={to_email} subject={subject}")
    return False


# ─── Dispatch helper (called by sensor_service) ────────────────────────────────
async def dispatch_alert_notifications(
    workshop_name: str,
    alert_message: str,
    owner_phone: Optional[str],
    owner_email: Optional[str],
    notify_sms: bool,
    notify_email: bool,
) -> dict:
    """
    Fire off SMS and/or email based on AlertConfig flags.
    Returns dict with booleans indicating what was attempted/sent.
    """
    sms_sent = False
    email_sent = False

    if notify_sms and owner_phone:
        sms_sent = await send_sms_alert(
            to_phone=owner_phone,
            message=alert_message,
            workshop_name=workshop_name,
        )

    if notify_email and owner_email:
        email_sent = await send_email_alert(
            to_email=owner_email,
            subject=f"[{workshop_name}] Alert: {alert_message[:60]}",
            body=alert_message,
        )

    return {"sms_sent": sms_sent, "email_sent": email_sent}
