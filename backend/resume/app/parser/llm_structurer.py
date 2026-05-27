"""LLM-based resume structuring — raw text → structured JSON using LiteLLM + Instructor."""

import os
from litellm import acompletion
import instructor
from instructor import AsyncInstructor

from backend.resume.app.config import get_settings
from shared.schemas.resume import StructuredResume

SYSTEM_PROMPT = """You are an expert resume parser and analyzer. Extract and structure all relevant information from the provided resume text.

INSTRUCTIONS:
1. Extract ALL skills mentioned (which includes all technical skills like Python, AWS, etc., frameworks, programming languages, tools AND soft skills like Leadership, Communication)
2. Identify the experience level based on total years: junior (0-2 years), mid (2-5 years), senior (5+ years)
3. Calculate total years of professional work experience accurately
4. List all technologies, frameworks, programming languages, and tools mentioned
5. Extract project details including name, description, and technologies used
6. Capture educational qualifications with degree, institution, graduation year and score if available
7. Document employment history with company, role, duration, and key responsibilities
8. Identify any career gaps, unexplained breaks, or concerns in the timeline
9. Write a concise 2-3 sentence professional summary highlighting key strengths and experience

IMPORTANT:
- Be thorough and extract ALL mentioned information
- For employment_timeline, list jobs in reverse chronological order (most recent first)
- If information is missing or unclear, use your best judgment or omit the field
- Deduplicate skills and technologies
- Calculate years_of_experience by summing up all employment durations"""


async def structure_resume_text(raw_text: str) -> StructuredResume:
    """
    Use LLM with Instructor to structure raw resume text into a validated StructuredResume.
    
    Args:
        raw_text: Raw text extracted from resume document
        
    Returns:
        StructuredResume: Validated and structured resume data
    """
    settings = get_settings()
    
    # Construct model string for LiteLLM
    model = f"{settings.llm_provider}/{settings.llm_model}"
    
    try:
        # Create instructor client from LiteLLM completion function
        client = instructor.from_litellm(acompletion)
        
        # Use instructor to get structured output
        structured_resume = await client.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse this resume and extract all information:\n\n{raw_text[:8000]}"}
            ],
            response_model=StructuredResume,
            temperature=0.2,
            max_retries=3
        )

        return structured_resume
            
    except Exception as e:
        # Fallback to basic parsing if LLM fails
        print(f"LLM structuring failed: {e}")
        import traceback
        traceback.print_exc()
        return _basic_parse(raw_text)


def _basic_parse(raw_text: str) -> StructuredResume:
    """
    Basic fallback parsing without LLM.
    Returns minimal structured data when LLM parsing fails.
    """
    lines = raw_text.split("\n")
    first_line = lines[0] if lines else "Resume"
    
    return StructuredResume(
        skills=[],
        experience_level="mid",
        years_of_experience=0.0,
        tech_stack=[],
        projects=[],
        education=[],
        employment_timeline=[],
        gaps=["Unable to parse resume - LLM service unavailable"],
        summary=first_line[:100],
        raw_text=raw_text,
    )
