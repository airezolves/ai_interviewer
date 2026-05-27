"""Match Scorer — compute resume-JD fit analysis using LLM with Pydantic validation."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import MatchAnalysis
from shared.schemas.resume import StructuredResume
from shared.schemas.kit import StructuredJD

SYSTEM_PROMPT = """You are an expert technical recruiter and hiring manager specializing in data science, machine learning, and engineering roles.

Your task is to analyze how well a candidate's resume matches a specific job description and provide a comprehensive fit analysis.

ANALYSIS INSTRUCTIONS:

1. **Overall Match Score (0-100)**:
   - Calculate a holistic score representing overall fit
   - Weight factors: required skills (40%), experience level (30%), nice-to-have skills (15%), tech stack alignment (15%)
   - 90-100: Exceptional fit, exceeds most requirements
   - 70-89: Strong fit, meets most requirements with minor gaps
   - 50-69: Moderate fit, meets core requirements but has notable gaps
   - 30-49: Weak fit, significant skill or experience gaps
   - 0-29: Poor fit, misaligned with role requirements

2. **Skill Matches**:
   - List ALL skills the candidate HAS that the JD requires (both required and nice-to-have)
   - Include exact matches and closely related skills (e.g., "PyTorch" matches "Deep Learning frameworks")
   - Prioritize required skills over nice-to-have
   - Use specific terminology from both resume and JD

3. **Skill Gaps**:
   - List required skills from the JD that the candidate's resume does NOT demonstrate
   - Prioritize critical gaps (required skills) over minor gaps (nice-to-have)
   - Be specific about technologies and tools, not vague categories
   - If a skill is partially present, don't list it as a gap

4. **Experience Fit**:
   - Provide a 2-4 sentence narrative assessment covering:
     * Years of experience alignment (candidate vs. JD requirement)
     * Relevance of past roles to the target role
     * Project complexity and scope match
     * Domain expertise alignment
   - Be specific with examples from the resume

5. **Level Calibration**:
   - Determine if the candidate is:
     * "underqualified": Less experience or skills than required (e.g., junior applying for senior)
     * "appropriate": Good fit for the level (experience and skills align)
     * "overqualified": Significantly exceeds requirements (e.g., senior applying for mid-level)
     * "unknown": Insufficient information to determine
   - Base this on years of experience, seniority signals, and scope of responsibilities

QUALITY GUIDELINES:
- Be objective and data-driven in your assessment
- Consider context: similar skills/technologies should count as matches
- Be thorough but concise in skill lists
- Provide specific evidence in experience_fit narrative
- Account for transferable skills and related experience
- Don't penalize for having additional skills beyond requirements

OUTPUT: Return structured JSON matching the MatchAnalysis schema."""


async def compute_match_score(
    resume: StructuredResume,
    jd: StructuredJD,
    role_type: str,
) -> MatchAnalysis:
    """
    Compute comprehensive match analysis between a candidate's resume and job description.
    
    Args:
        resume: Structured resume data from the candidate
        jd: Structured job description data
        role_type: Type of role (e.g., "data_scientist", "ml_engineer")
        
    Returns:
        MatchAnalysis: Validated match analysis with scoring and detailed breakdown
    """
    client = get_llm_client()

    # Build comprehensive context for LLM
    prompt = f"""Analyze the fit between this candidate and job requirement:

═══ CANDIDATE PROFILE ═══
Experience Level: {resume.experience_level}
Years of Experience: {resume.years_of_experience}

Skills ({len(resume.skills)} total):
{', '.join(resume.skills[:30])}

Education:
{chr(10).join(f"- {edu.degree} from {edu.institution} ({edu.year or 'N/A'})" for edu in resume.education[:3]) if resume.education else "Not specified"}

Employment History ({len(resume.employment_timeline)} positions):
{chr(10).join(f"- {emp.role} at {emp.company} ({emp.duration})" for emp in resume.employment_timeline[:4]) if resume.employment_timeline else "Not specified"}

Projects ({len(resume.projects)} total):
{chr(10).join(f"- {proj.name}: {proj.description[:100]}..." for proj in resume.projects[:3]) if resume.projects else "Not specified"}

Gaps or Concerns:
{chr(10).join(f"- {gap}" for gap in resume.gaps[:4]) if resume.gaps else "None identified"}

Professional Summary:
{resume.summary}

═══ JOB REQUIREMENTS ═══
Role Type: {role_type}
Required Seniority: {jd.seniority}

Required Skills ({len(jd.required_skills)} total):
{', '.join(jd.required_skills[:20])}

Nice-to-Have Skills ({len(jd.nice_to_have_skills)} total):
{', '.join(jd.nice_to_have_skills[:15])}

Key Responsibilities ({len(jd.responsibilities)} total):
{chr(10).join(f"- {resp}" for resp in jd.responsibilities[:5])}

Team Context:
{jd.team_context or "Not specified"}

Company Info:
{jd.company_info or "Not specified"}

═══ TASK ═══
Provide a comprehensive match analysis following the instructions in your system prompt."""

    try:
        data = await client.pydantic_generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_model=MatchAnalysis,
            temperature=0.3,
            max_retries=3
        )
        return data
        
    except Exception as e:
        # Fallback: Basic algorithmic match without LLM
        print(f"Match scoring failed, using fallback: {e}")
        import traceback
        traceback.print_exc()
        
        # Calculate basic matches
        resume_skills_lower = {s.lower().strip() for s in resume.skills}
        required_skills_lower = {s.lower().strip() for s in jd.required_skills}
        nice_to_have_lower = {s.lower().strip() for s in jd.nice_to_have_skills}
        
        matched_required = resume_skills_lower & required_skills_lower
        matched_nice = resume_skills_lower & nice_to_have_lower
        gaps = required_skills_lower - resume_skills_lower
        
        # Basic scoring algorithm
        required_score = (len(matched_required) / max(len(required_skills_lower), 1)) * 70
        nice_score = (len(matched_nice) / max(len(nice_to_have_lower), 1)) * 20
        experience_score = 10 if resume.experience_level == jd.seniority else 5
        score = min(100.0, required_score + nice_score + experience_score)
        
        # Level calibration
        level_map = {"junior": 0, "mid": 1, "senior": 2}
        resume_level = level_map.get(resume.experience_level, 1)
        jd_level = level_map.get(jd.seniority, 1)
        
        if resume_level < jd_level:
            calibration = "underqualified"
        elif resume_level > jd_level:
            calibration = "overqualified"
        else:
            calibration = "appropriate"
        
        return MatchAnalysis(
            overall_match_score=round(score, 1),
            skill_matches=[s for s in jd.required_skills if s.lower() in resume_skills_lower][:15],
            skill_gaps=[s for s in jd.required_skills if s.lower() not in resume_skills_lower][:15],
            experience_fit=f"Candidate has {resume.years_of_experience} years as {resume.experience_level}, applying for {jd.seniority} role. Basic algorithmic match (LLM unavailable).",
            level_calibration=calibration,
        )
