"""JD analyzer using the per-user model factory."""

from shared.llm import get_instructor_client
from shared.schemas.kit import StructuredJD


SYSTEM_PROMPT = """You are an expert job description analyzer.

Extract:
  - required_skills, nice_to_have_skills (deduped, exact terminology)
  - seniority (junior | mid | senior)
  - responsibilities (bullet list)
  - team_context, company_info (concise)

Output STRICT StructuredJD."""


async def analyze_jd(jd_text: str) -> StructuredJD:
    client, model, extra = get_instructor_client(json_mode=True)
    return client.chat.completions.create(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Job description:\n\n{jd_text[:8000]}\n\nExtract StructuredJD."},
        ],
        response_model=StructuredJD,
        max_retries=2,
        temperature=0.2,
        **extra,
    )
