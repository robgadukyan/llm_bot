"""Prompt templates for the teaching assistant agent."""

SYSTEM_PROMPT = """You are an agentic teaching-assistant system for an NLP course.
You must produce practical lesson-planning content grounded in the provided slides.
When a point is supported by slides, mark it with a slide reference like [Slide 2].
When a point comes from web resources, mark it as [Web].
Do not invent citations, URLs, or slide numbers.
Write clearly for university instructors.
"""


def slide_summary_prompt(slide_context: str, output_language: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Language: {output_language}

From the slide text below, create:
1. A short lecture title.
2. A 5-7 sentence slide-grounded summary.
3. The main topic keywords for web search.

Slide text:
{slide_context}
""",
        },
    ]


def concept_map_prompt(slide_context: str, output_language: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Language: {output_language}

Create a compact concept map from these slides. Use this exact structure:
- Main concepts
- Relationships between concepts
- Likely prerequisites
- Possible misconceptions

Include slide references where possible.

Slides:
{slide_context}
""",
        },
    ]


def teaching_plan_prompt(
    slide_context: str,
    slide_summary: str,
    concept_map: str,
    resources_md: str,
    audience: str,
    duration_minutes: int,
    output_language: str,
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Create a complete lesson-planning package in {output_language}.

Audience: {audience}
Duration: {duration_minutes} minutes

Slide-grounded summary:
{slide_summary}

Concept map:
{concept_map}

Web resources available:
{resources_md}

Slide text for grounding:
{slide_context}

Required output sections:
# Title
# Audience and Duration
# Learning Objectives
# Timed Teaching Plan
Use a realistic time table whose total is exactly {duration_minutes} minutes.
# Worked Example
# Student Exercise
# Recap / Exit Ticket
# Supporting Web Resources
# Grounding Notes
# Email Body

Rules:
- Mark slide-based claims with [Slide X].
- Mark external-resource suggestions with [Web].
- Keep timing realistic.
- Include at least one exercise.
- Include a professional email body that can be sent to the instructor or recipient.
""",
        },
    ]


def revision_prompt(package_md: str, duration_minutes: int, output_language: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Language: {output_language}

Review the package below for realism, clarity, and grounding.
Return a short revision checklist with:
- timing check,
- grounding check,
- missing information,
- final quality verdict.

The timed plan must total {duration_minutes} minutes.

Package:
{package_md}
""",
        },
    ]
