"""Email service interface (SendGrid/SMTP) — placeholder, configurable, never crashes."""
import logging
from typing import Optional
from abc import ABC, abstractmethod
from settings_service import get_setting

log = logging.getLogger(__name__)


class IEmailProvider(ABC):
    name: str
    configured: bool

    @abstractmethod
    async def send_email(self, to: str, subject: str, html: str, attachments: Optional[list] = None) -> bool:
        ...


class SendGridProvider(IEmailProvider):
    name = "sendgrid"

    def __init__(self, api_key: Optional[str], sender_email: Optional[str], sender_name: Optional[str]):
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.configured = bool(api_key and sender_email)

    async def send_email(self, to: str, subject: str, html: str, attachments: Optional[list] = None) -> bool:
        if not self.configured:
            log.info("SendGrid not configured; skipping email send.")
            return False
        # Lazy import to avoid hard dependency if unused
        try:
            import httpx
            payload = {
                "personalizations": [{"to": [{"email": to}], "subject": subject}],
                "from": {"email": self.sender_email, "name": self.sender_name or "Business Radar AI"},
                "content": [{"type": "text/html", "value": html}],
            }
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
            ok = 200 <= r.status_code < 300
            if not ok:
                log.warning(f"SendGrid send failed: {r.status_code} {r.text}")
            return ok
        except Exception as e:
            log.warning(f"SendGrid send exception: {e}")
            return False


class SMTPProvider(IEmailProvider):
    name = "smtp"

    def __init__(self, host, port, user, password, sender_email, sender_name):
        self.host = host
        self.port = int(port) if port else 587
        self.user = user
        self.password = password
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.configured = bool(host and sender_email)

    async def send_email(self, to: str, subject: str, html: str, attachments: Optional[list] = None) -> bool:
        if not self.configured:
            log.info("SMTP not configured; skipping email send.")
            return False
        # Minimal SMTP send (placeholder)
        try:
            import aiosmtplib
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to
            msg["Subject"] = subject
            msg.add_alternative(html, subtype="html")
            await aiosmtplib.send(msg, hostname=self.host, port=self.port, username=self.user, password=self.password, start_tls=True)
            return True
        except Exception as e:
            log.warning(f"SMTP send exception: {e}")
            return False


async def get_email_provider() -> Optional[IEmailProvider]:
    provider = (await get_setting("email_provider")) or "sendgrid"
    sender_email = await get_setting("sender_email")
    sender_name = await get_setting("sender_name") or "Business Radar AI"
    if provider == "sendgrid":
        api_key = await get_setting("sendgrid_api_key")
        return SendGridProvider(api_key, sender_email, sender_name)
    if provider == "smtp":
        host = await get_setting("smtp_host")
        port = await get_setting("smtp_port")
        user = await get_setting("smtp_user")
        password = await get_setting("smtp_password")
        return SMTPProvider(host, port, user, password, sender_email, sender_name)
    return None


async def send_email_safe(to: str, subject: str, html: str) -> dict:
    p = await get_email_provider()
    if not p or not getattr(p, "configured", False):
        return {"sent": False, "reason": "email_provider_not_configured"}
    ok = await p.send_email(to, subject, html)
    return {"sent": ok, "provider": p.name}
