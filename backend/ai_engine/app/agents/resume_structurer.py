"""Resume structurer using the per-user model factory.

Replaces the old `backend/resume/app/parser/llm_structurer.py` (still
present until cleanup) so resume parsing also honours the recruiter's
active LLM provider.
"""

from shared.llm import get_instructor_client
from shared.schemas.resume import StructuredResume


SYSTEM_PROMPT = """You are an expert resume parser.

Extract ALL skills, experience_level (junior|mid|senior), years_of_experience,
projects, education, employment_timeline, gaps, and a 2-3 sentence summary.

Output STRICT StructuredResume."""


async def structure_resume(raw_text: str) -> StructuredResume:
    client, model, extra = get_instructor_client(json_mode=True)
    return client.chat.completions.create(  # type: ignore[attr-defined]
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Resume text:\n\n{raw_text[:8000]}\n\nProduce the StructuredResume now."},
        ],
        response_model=StructuredResume,
        max_retries=2,
        temperature=0.2,
        **extra,
    )
