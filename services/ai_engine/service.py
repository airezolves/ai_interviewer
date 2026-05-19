"""AI Engine service — core generation logic."""

import asyncio
import json

from shared.utils.logger import get_logger
from shared.middleware.error_handler import ServiceException
from services.ai_engine.llm.claude_client import ClaudeClient
from services.ai_engine.llm.openai_client import OpenAIClient
from services.ai_engine.prompts.questions import get_questions_prompt
from services.ai_engine.prompts.assessment import get_assessment_prompt
from services.ai_engine.prompts.rubric import get_rubric_prompt
from services.ai_engine.prompts.red_flags import get_red_flags_prompt
from services.ai_engine.prompts.flow_guide import get_flow_guide_prompt
from services.ai_engine.config.settings import get_ai_engine_settings

logger = get_logger(__name__)
settings = get_ai_engine_settings()

JD_ANALYSIS_PROMPT = """Analyze this job description and extract structured information.

Job Description:
{jd_text}

Extract:
1. "role_title": The job title
2. "seniority_level": "junior" | "mid" | "senior" | "lead" | "principal"
3. "required_skills": List of required technical skills
4. "nice_to_haves": List of nice-to-have skills
5. "responsibilities": List of key responsibilities (max 8)
6. "team_context": Description of the team/org (if mentioned)
7. "industry": Industry/domain
8. "company_size": Startup/Mid/Enterprise (infer from context)

Return ONLY valid JSON.
"""


class AIEngineService:
    """Core AI generation service. Orchestrates all LLM calls."""

    def __init__(self):
        if settings.DEFAULT_LLM_PROVIDER == "anthropic":
            self.llm = ClaudeClient()
        else:
            self.llm = OpenAIClient()

    async def analyze_jd(self, jd_text: str) -> dict:
        """Analyze and structure a job description."""
        prompt = JD_ANALYSIS_PROMPT.format(jd_text=jd_text[:5000])
        try:
            return await self.llm.generate_json(prompt, max_tokens=2000)
        except Exception as e:
            logger.error("jd_analysis_failed", error=str(e))
            raise ServiceException(f"Failed to analyze JD: {e}", status_code=500)

    async def generate_questions(self, jd_analysis: dict, resume_data: dict, role_type: str) -> dict:
        """Generate interview questions with model answers."""
        prompt = get_questions_prompt(jd_analysis, resume_data, role_type)
        try:
            return await self.llm.generate_json(prompt, max_tokens=settings.MAX_TOKENS_QUESTIONS)
        except Exception as e:
            logger.error("question_generation_failed", error=str(e))
            raise ServiceException(f"Failed to generate questions: {e}", status_code=500)

    async def generate_assessment(self, jd_analysis: dict, resume_data: dict, role_type: str) -> dict:
        """Generate practical assessment."""
        prompt = get_assessment_prompt(jd_analysis, resume_data, role_type)
        try:
            return await self.llm.generate_json(prompt, max_tokens=settings.MAX_TOKENS_ASSESSMENT)
        except Exception as e:
            logger.error("assessment_generation_failed", error=str(e))
            raise ServiceException(f"Failed to generate assessment: {e}", status_code=500)

    async def generate_rubric(self, jd_analysis: dict, resume_data: dict, role_type: str) -> dict:
        """Generate scoring rubric."""
        prompt = get_rubric_prompt(jd_analysis, resume_data, role_type)
        try:
            return await self.llm.generate_json(prompt, max_tokens=settings.MAX_TOKENS_RUBRIC)
        except Exception as e:
            logger.error("rubric_generation_failed", error=str(e))
            raise ServiceException(f"Failed to generate rubric: {e}", status_code=500)

    async def generate_red_flags(self, jd_analysis: dict, resume_data: dict, role_type: str) -> dict:
        """Identify candidate red flags."""
        prompt = get_red_flags_prompt(jd_analysis, resume_data, role_type)
        try:
            return await self.llm.generate_json(prompt, max_tokens=settings.MAX_TOKENS_RED_FLAGS)
        except Exception as e:
            logger.error("red_flags_generation_failed", error=str(e))
            raise ServiceException(f"Failed to generate red flags: {e}", status_code=500)

    async def generate_flow_guide(self, jd_analysis: dict, resume_data: dict, role_type: str) -> dict:
        """Generate interview flow guide."""
        prompt = get_flow_guide_prompt(jd_analysis, resume_data, role_type)
        try:
            return await self.llm.generate_json(prompt, max_tokens=settings.MAX_TOKENS_FLOW_GUIDE)
        except Exception as e:
            logger.error("flow_guide_generation_failed", error=str(e))
            raise ServiceException(f"Failed to generate flow guide: {e}", status_code=500)

    async def generate_full_kit(
        self, jd_text: str, resume_data: dict, role_type: str
    ) -> dict:
        """Generate a complete interview kit with parallel LLM calls."""
        logger.info("generating_full_kit", role_type=role_type)

        # Step 1: Analyze JD (sequential — needed for subsequent steps)
        jd_analysis = await self.analyze_jd(jd_text)
        logger.info("jd_analysis_complete")

        # Step 2: Generate all sections in parallel
        results = await asyncio.gather(
            self.generate_questions(jd_analysis, resume_data, role_type),
            self.generate_assessment(jd_analysis, resume_data, role_type),
            self.generate_rubric(jd_analysis, resume_data, role_type),
            self.generate_red_flags(jd_analysis, resume_data, role_type),
            self.generate_flow_guide(jd_analysis, resume_data, role_type),
            return_exceptions=True,
        )

        # Handle any failures gracefully
        questions, assessment, rubric, red_flags, flow_guide = results

        def safe_result(result, section_name: str) -> dict:
            if isinstance(result, Exception):
                logger.error(f"{section_name}_failed_in_kit", error=str(result))
                return {"error": f"Failed to generate {section_name}", "detail": str(result)}
            return result

        kit = {
            "jd_analysis": jd_analysis,
            "questions": safe_result(questions, "questions"),
            "assessment": safe_result(assessment, "assessment"),
            "rubric": safe_result(rubric, "rubric"),
            "red_flags": safe_result(red_flags, "red_flags"),
            "flow_guide": safe_result(flow_guide, "flow_guide"),
        }

        logger.info("full_kit_generated")
        return kit
