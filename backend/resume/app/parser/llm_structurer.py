"""LLM-based resume structuring — raw text → structured JSON."""

import json
from anthropic import AsyncAnthropic

from backend.resume.app.config import get_settings
from shared.schemas.resume import StructuredResume

SYSTEM_PROMPT = """You are a resume parser. Given raw text extracted from a resume, 
output a structured JSON with the following fields:
- skills: list of technical and soft skills
- experience_level: "junior" (0-2 years), "mid" (2-5 years), or "senior" (5+ years)
- years_of_experience: estimated total years
- tech_stack: list of technologies/tools/frameworks
- projects: list of {name, description, technologies}
- education: list of {degree, institution, year, field}
- employment_timeline: list of {company, role, duration, responsibilities}
- gaps: list of concerns or gaps identified
- summary: 2-3 sentence professional summary

Output ONLY valid JSON, no markdown fences or extra text."""


async def structure_resume_text(raw_text: str) -> StructuredResume:
    """Use LLM to structure raw resume text into a StructuredResume."""
    settings = get_settings()

    if not settings.anthropic_api_key:
        # Fallback: return basic structure without LLM
        return _basic_parse(raw_text)

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Parse this resume:\n\n{raw_text[:8000]}"}
        ],
    )

    response_text = message.content[0].text

    try:
        data = json.loads(response_text)
        return StructuredResume(**data, raw_text=raw_text)
    except (json.JSONDecodeError, Exception):
        return _basic_parse(raw_text)


def _basic_parse(raw_text: str) -> StructuredResume:
    """Basic fallback parsing without LLM."""
    lines = raw_text.split("\n")
    return StructuredResume(
        skills=[],
        experience_level="mid",
        years_of_experience=0,
        tech_stack=[],
        projects=[],
        education=[],
        employment_timeline=[],
        gaps=[],
        summary=lines[0] if lines else "",
        raw_text=raw_text,
    )
