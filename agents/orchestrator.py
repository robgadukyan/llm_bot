"""Agent orchestrator: slide parsing -> LLM -> web search -> revision -> package."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from pathlib import Path

from agents.prompts import (
    concept_map_prompt,
    revision_prompt,
    slide_summary_prompt,
    teaching_plan_prompt,
)
from llm_backend import LLMError, generate
from tools.logger import log_event
from tools.slides import chunks_to_context, parse_slides, rough_summary
from tools.web_search import resources_to_markdown, search_web


@dataclass(frozen=True)
class LessonRequest:
    duration_minutes: int
    audience: str
    output_language: str
    recipient_email: str


@dataclass(frozen=True)
class AgentResult:
    package_md: str
    email_subject: str
    email_body: str
    slide_count: int
    web_error: str | None


class TeachingAssistantAgent:
    def __init__(self, chat_id: int | str = "local") -> None:
        self.chat_id = chat_id
        self.allow_fallback = os.getenv("ALLOW_LLM_FALLBACK", "false").lower() == "true"

    def _generate_or_fallback(self, messages: list[dict[str, str]], fallback: str, max_tokens: int = 1200) -> str:
        try:
            return generate(messages, temperature=0.2, max_tokens=max_tokens)
        except LLMError as exc:
            log_event(self.chat_id, "llm_error", {"error": str(exc)})
            if self.allow_fallback:
                return fallback
            raise

    @staticmethod
    def _search_query_from_summary(summary: str) -> str:
        # Prefer a short title line if the model gave one; otherwise use frequent content words.
        first_line = next((line for line in summary.splitlines() if line.strip()), "")
        first_line = re.sub(r"[#:*_`\-]+", " ", first_line).strip()
        if 8 <= len(first_line) <= 120:
            return first_line
        words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", summary)
        return " ".join(words[:8]) or "NLP lecture teaching resources"

    def run(self, slide_path: str | Path, request: LessonRequest) -> AgentResult:
        log_event(self.chat_id, "workflow_started", {"slide_path": str(slide_path)})

        chunks = parse_slides(slide_path)
        slide_context = chunks_to_context(chunks)
        fallback_summary = "Fallback slide summary:\n" + rough_summary(chunks)

        summary = self._generate_or_fallback(
            slide_summary_prompt(slide_context, request.output_language),
            fallback=fallback_summary,
            max_tokens=900,
        )
        log_event(self.chat_id, "slide_summary_done", {"chars": len(summary)})

        concept_map = self._generate_or_fallback(
            concept_map_prompt(slide_context, request.output_language),
            fallback="- Main concepts: extracted from slide titles and bullet points.\n- Prerequisites: basic NLP and machine learning vocabulary.",
            max_tokens=900,
        )
        log_event(self.chat_id, "concept_map_done", {"chars": len(concept_map)})

        query = self._search_query_from_summary(summary)
        resources, web_error = search_web(query, max_results=5)
        resources_md = resources_to_markdown(resources, web_error)
        log_event(self.chat_id, "web_search_done", {"query": query, "results": len(resources), "error": web_error})

        plan = self._generate_or_fallback(
            teaching_plan_prompt(
                slide_context=slide_context,
                slide_summary=summary,
                concept_map=concept_map,
                resources_md=resources_md,
                audience=request.audience,
                duration_minutes=request.duration_minutes,
                output_language=request.output_language,
            ),
            fallback=self._fallback_plan(request, summary, concept_map, resources_md, chunks=len(chunks)),
            max_tokens=2200,
        )
        log_event(self.chat_id, "teaching_plan_done", {"chars": len(plan)})

        revision = self._generate_or_fallback(
            revision_prompt(plan, request.duration_minutes, request.output_language),
            fallback="Revision checklist: timing should be verified manually; grounding tags are included where available; web search may need rerun if no results returned.",
            max_tokens=700,
        )

        package_md = f"""{plan}

---

# Agent Revision Checklist
{revision}

# Runtime Notes
- Slides parsed: {len(chunks)}
- Web search status: {web_error or 'OK'}
- Email requires explicit /send confirmation in Telegram.
""".strip()

        subject = self._subject_from_package(package_md)
        email_body = self._email_body_from_package(package_md)
        log_event(self.chat_id, "workflow_finished", {"subject": subject})
        return AgentResult(
            package_md=package_md,
            email_subject=subject,
            email_body=email_body,
            slide_count=len(chunks),
            web_error=web_error,
        )

    @staticmethod
    def _subject_from_package(package_md: str) -> str:
        for line in package_md.splitlines():
            clean = line.strip("# *")
            if clean and len(clean) < 90 and clean.lower() not in {"title", "email body"}:
                return f"Lesson plan: {clean}"
        return "Lesson plan generated from lecture slides"

    @staticmethod
    def _email_body_from_package(package_md: str) -> str:
        marker = "# Email Body"
        if marker in package_md:
            candidate = package_md.split(marker, 1)[1].split("\n# ", 1)[0].strip()
            if candidate:
                return candidate
        return (
            "Dear colleague,\n\n"
            "Please find below the generated lesson-planning package prepared from the uploaded slides.\n\n"
            f"{package_md}\n\nBest regards,\nAgentic Teaching Assistant"
        )

    @staticmethod
    def _fallback_plan(
        request: LessonRequest,
        summary: str,
        concept_map: str,
        resources_md: str,
        chunks: int,
    ) -> str:
        half = max(10, request.duration_minutes // 2)
        remaining = request.duration_minutes - half
        return f"""# Title
Slide-Based Teaching Plan

# Audience and Duration
Audience: {request.audience}
Duration: {request.duration_minutes} minutes
Language: {request.output_language}

# Learning Objectives
By the end of the class, students should be able to:
1. Explain the main ideas presented in the slides.
2. Connect core concepts to examples and applications.
3. Complete a short practice activity using the lecture material.

# Slide Summary
{summary}

# Concept Map
{concept_map}

# Timed Teaching Plan
| Time | Activity | Grounding |
|---:|---|---|
| {half} min | Instructor explanation of the main slide concepts | [Slide 1-{chunks}] |
| {remaining} min | Guided exercise, discussion, recap, and exit ticket | [Slide 1-{chunks}] |

# Student Exercise
Ask students to choose one concept from the slides, define it in their own words, and give one practical example.

# Supporting Web Resources
{resources_md}

# Grounding Notes
The fallback plan uses extracted slide text and should be manually improved after the local LLM server is available.

# Email Body
Dear colleague,

Please find the generated slide-based lesson plan below. It includes objectives, timing, an exercise, supporting resources, and grounding notes.

Best regards,
Agentic Teaching Assistant
"""
