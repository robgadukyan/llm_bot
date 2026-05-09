"""Local LLM backend wrapper.

This module talks to a local OpenAI-compatible chat-completions server.
It works with vLLM, llama.cpp server, and llama-cpp-python server as long as
/v1/chat/completions is available.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMError(RuntimeError):
    """Raised when the local LLM server cannot produce a response."""


@dataclass(frozen=True)
class LocalLLMConfig:
    base_url: str
    model: str
    api_key: str = "EMPTY"
    timeout_seconds: float = 120.0

    @staticmethod
    def from_env() -> "LocalLLMConfig":
        return LocalLLMConfig(
            base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:8000/v1"),
            model=os.getenv("LLM_MODEL", "local-model"),
            api_key=os.getenv("LLM_API_KEY", "EMPTY"),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
        )


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


def generate(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 1400,
    config: LocalLLMConfig | None = None,
) -> str:
    """Generate text using the local LLM server.

    Parameters
    ----------
    messages:
        OpenAI-style chat messages, e.g. [{"role": "user", "content": "..."}].
    temperature:
        Sampling temperature. Keep low for teaching-plan reliability.
    max_tokens:
        Maximum number of generated tokens.
    config:
        Optional explicit backend configuration. Usually read from environment.
    """
    cfg = config or LocalLLMConfig.from_env()
    url = _chat_completions_url(cfg.base_url)
    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"

    try:
        with httpx.Client(timeout=cfg.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:  # noqa: BLE001 - converted to domain-specific error
        raise LLMError(f"Local LLM call failed: {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # noqa: BLE001
        raise LLMError(f"Unexpected LLM response format: {data}") from exc
