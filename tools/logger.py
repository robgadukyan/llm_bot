"""Tiny JSONL logger for status/debugging."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


def log_event(chat_id: int | str, event: str, details: dict[str, Any] | None = None) -> None:
    log_dir = Path(os.getenv("LOG_DIR", "data/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "chat_id": str(chat_id),
        "event": event,
        "details": details or {},
    }
    with (log_dir / f"chat_{chat_id}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
