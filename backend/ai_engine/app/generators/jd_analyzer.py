"""JD Analyzer — parse job descriptions into structured data using LLM with Pydantic validation."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import StructuredJD

SYSTEM_PROMPT = """You are an expert job description analyzer specializing in technical hiring and data/engineering roles.

Your task is to extract and structure all relevant information from job descriptions to enable effective interview preparation.

EXTRACTION INSTRUCTIONS:

1. **Required Skills**: Extract ALL mandatory qualifications, skills, and technologies
   - Programming languages (Python, R, SQL, etc.)
   - Tools and frameworks (Pandas, TensorFlow, Spark, etc.)
   - Years of experience requirements
   - Specific certifications or degrees
   - Domain knowledge requirements
   - Technical competencies explicitly marked as "required" or "must have"

2. **Nice-to-Have Skills**: Extract preferred/bonus qualifications
   - Skills mentioned as "preferred", "plus", "bonus", or "nice to have"
   - Additional technologies that would be beneficial
   - Extra certifications or experiences that are advantageous but not mandatory

3. **Seniority Level**: Determine the appropriate level
   - "junior": 0-2 years experience, entry-level, junior/associate titles
   - "mid": 2-5 years experience, mid-level responsibilities, some autonomy
   - "senior": 5+ years experience, senior/lead/principal titles, leadership/mentorship responsibilities

4. **Responsibilities**: List all key duties and expectations
   - Day-to-day tasks
   - Project ownership and deliverables
   - Collaboration and communication expectations
   - Technical and non-technical responsibilities

5. **Team Context**: Capture team-related information
   - Team size and structure
   - Reporting relationships (who you report to, who reports to you)
   - Cross-functional collaboration details
   - Department or business unit information

6. **Company Info**: Extract relevant company details
   - Company name and industry
   - Company size, stage (startup, growth, enterprise)
   - Mission, values, or culture highlights
   - Product or service description
   - Geographic location or remote work policy

QUALITY GUIDELINES:
- Be thorough and extract ALL mentioned information
- Distinguish clearly between required vs. nice-to-have
- Use exact terminology from the JD when possible
- If information is unclear or missing, make reasonable inferences or omit
- Remove duplicates from skill lists
- Prioritize accuracy over completeness

OUTPUT: Return structured JSON matching the StructuredJD schema."""


async def analyze_jd(jd_text: str) -> StructuredJD:
    """
    Analyze a job description into structured format using LLM with Pydantic validation.
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        StructuredJD: Validated and structured job description data
    """
    client = get_llm_client()

    try:
        data = await client.pydantic_generate(
            prompt=f"Analyze this job description and extract all structured information:\n\n{jd_text[:8000]}",
            system=SYSTEM_PROMPT,
            response_model=StructuredJD,
            temperature=0.2,
            max_retries=3
        )

        return data
    except Exception as e:
        # Fallback: return basic structure with error indication
        print(f"JD analysis failed: {e}")
        import traceback
        traceback.print_exc()
        
        return StructuredJD(
            required_skills=["Unable to parse - LLM service unavailable"],
            nice_to_have_skills=[],
            seniority="mid",
            responsibilities=["Could not extract responsibilities"],
            team_context="Information unavailable",
            company_info="Information unavailable",
        )
