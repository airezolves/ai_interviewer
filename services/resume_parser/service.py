"""Resume Parser service business logic."""

import json
import uuid
from pathlib import Path

import anthropic

from shared.utils.logger import get_logger
from shared.middleware.error_handler import ServiceException
from services.resume_parser.parsers.pdf_parser import extract_text_from_pdf
from services.resume_parser.parsers.docx_parser import extract_text_from_docx
from services.resume_parser.schemas import ParsedResume
from services.resume_parser.config.settings import get_resume_parser_settings

logger = get_logger(__name__)
settings = get_resume_parser_settings()

STRUCTURING_PROMPT = """You are a resume parser. Given raw text extracted from a resume, extract and structure the information into a JSON format.

Extract the following fields:
- name: Full name
- email: Email address
- phone: Phone number
- location: City/Country
- summary: Professional summary (1-2 sentences)
- total_experience_years: Total years of professional experience (number)
- current_role: Most recent job title
- skills: All skills mentioned (list of strings)
- technical_skills: Technical/hard skills only (list of strings)
- soft_skills: Soft skills mentioned or implied (list of strings)
- experience: List of work experiences, each with {company, role, duration, highlights: []}
- education: List of education entries, each with {institution, degree, year}
- projects: Notable projects, each with {name, description, tech_stack: []}
- certifications: List of certification names
- gaps: Any employment gaps identified (list of descriptions)
- strengths: Key strengths based on experience (list of 3-5 items)
- concerns: Potential concerns for an interviewer (list of 2-3 items)

Return ONLY valid JSON matching this schema. No markdown, no explanation.

Resume text:
{resume_text}"""


class ResumeParserService:
    """Handles resume parsing and structuring."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def parse_resume(self, file_bytes: bytes, filename: str) -> tuple[str, ParsedResume]:
        """Parse a resume file and return structured data."""
        # Step 1: Extract raw text based on file type
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            raw_text = extract_text_from_pdf(file_bytes)
        elif extension in (".docx", ".doc"):
            raw_text = extract_text_from_docx(file_bytes)
        else:
            raise ServiceException(f"Unsupported file format: {extension}", status_code=400)

        if not raw_text or len(raw_text) < 50:
            raise ServiceException(
                "Could not extract sufficient text from the resume. Please ensure the file is not image-based.",
                status_code=400,
            )

        logger.info("resume_text_extracted", filename=filename, text_length=len(raw_text))

        # Step 2: Structure with LLM
        structured_data = await self._structure_with_llm(raw_text)

        return raw_text, structured_data

    async def _structure_with_llm(self, raw_text: str) -> ParsedResume:
        """Use Claude to structure raw resume text into structured JSON."""
        prompt = STRUCTURING_PROMPT.format(resume_text=raw_text[:8000])  # Limit input size

        try:
            response = await self.client.messages.create(
                model=settings.DEFAULT_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()

            # Clean up potential markdown code fences
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            data = json.loads(content)
            return ParsedResume(**data)

        except json.JSONDecodeError as e:
            logger.error("llm_json_parse_error", error=str(e))
            # Return partial data on parse failure
            return ParsedResume(summary="Failed to fully parse resume. Raw text available.")

        except Exception as e:
            logger.error("llm_structuring_error", error=str(e))
            raise ServiceException(f"Failed to structure resume: {str(e)}", status_code=500)
