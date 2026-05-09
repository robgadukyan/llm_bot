"""Small helper for checking local configuration before the demo."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

required = [
    "TELEGRAM_BOT_TOKEN",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "SMTP_HOST",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM",
]

missing = [key for key in required if not os.getenv(key)]
if missing:
    print("Missing environment variables:")
    for key in missing:
        print(f"- {key}")
    raise SystemExit(1)

print("Environment looks complete.")
