"""Web-search tool for the agent.

The tool returns only URLs actually returned by the search provider. If search fails,
it returns a structured error instead of inventing references.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class WebResource:
    title: str
    url: str
    snippet: str
    justification: str


def _compact(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def _ddgs_text(query: str, max_results: int) -> Iterable[dict]:
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except Exception:  # pragma: no cover - alternative package name
        from ddgs import DDGS  # type: ignore

    with DDGS() as ddgs:
        yield from ddgs.text(query, max_results=max_results)


def search_web(query: str, max_results: int = 5) -> tuple[list[WebResource], str | None]:
    if not query.strip():
        return [], "Empty search query."

    resources: list[WebResource] = []
    try:
        for result in _ddgs_text(query, max_results=max_results):
            title = _compact(result.get("title", "Untitled"), 120)
            url = result.get("href") or result.get("url") or ""
            body = _compact(result.get("body") or result.get("snippet") or "")
            if not url:
                continue
            resources.append(
                WebResource(
                    title=title,
                    url=url,
                    snippet=body,
                    justification="Useful supporting reading because it expands or illustrates the lecture topic.",
                )
            )
    except Exception as exc:  # noqa: BLE001
        return [], f"Web search failed: {exc}"

    if not resources:
        return [], "No web resources were found."
    return resources[:max_results], None


def resources_to_markdown(resources: list[WebResource], error: str | None = None) -> str:
    if error and not resources:
        return f"Web search status: {error}"
    lines = []
    for idx, item in enumerate(resources, start=1):
        lines.append(
            f"{idx}. [{item.title}]({item.url}) - {item.snippet} Justification: {item.justification}"
        )
    if error:
        lines.append(f"\nSearch warning: {error}")
    return "\n".join(lines)
