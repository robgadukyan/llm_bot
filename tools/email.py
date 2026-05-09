"""Email tool with explicit SMTP configuration."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class SMTPConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str

    @staticmethod
    def from_env() -> "SMTPConfig":
        return SMTPConfig(
            host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            sender=os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME", ""),
        )


def build_email_body(package_md: str) -> str:
    return (
        "Dear colleague,\n\n"
        "Please find below the generated lesson-planning package prepared from the uploaded lecture slides.\n\n"
        f"{package_md}\n\n"
        "Best regards,\n"
        "Agentic Telegram Teaching Assistant"
    )


def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachment_path: str | Path | None = None,
    config: SMTPConfig | None = None,
) -> None:
    cfg = config or SMTPConfig.from_env()
    if not all([cfg.host, cfg.port, cfg.username, cfg.password, cfg.sender]):
        raise RuntimeError("SMTP is not configured. Check SMTP_* variables in .env.")
    if "@" not in to_email:
        raise ValueError("Recipient email is missing or invalid.")

    msg = EmailMessage()
    msg["From"] = cfg.sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        path = Path(attachment_path)
        data = path.read_bytes()
        msg.add_attachment(
            data,
            maintype="text",
            subtype="markdown",
            filename=path.name,
        )

    with smtplib.SMTP(cfg.host, cfg.port) as server:
        server.starttls()
        server.login(cfg.username, cfg.password)
        server.send_message(msg)
