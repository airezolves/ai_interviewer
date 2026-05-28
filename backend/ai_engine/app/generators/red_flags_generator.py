"""Red Flags Generator — identify concerns and create diplomatic probe questions."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import RedFlag, RedFlagSet

SYSTEM_PROMPT = """You are a highly experienced senior hiring manager with 15+ years of experience conducting interviews and evaluating candidates.
Your task is to identify potential concerns or areas requiring deeper investigation based on the candidate's resume and job requirements.

## YOUR APPROACH:
1. Analyze the resume for patterns, gaps, or inconsistencies that may indicate concerns
2. Compare resume against JD requirements to identify skill/experience mismatches
3. Look for career progression patterns (frequent job changes, stagnant roles, unclear impact)
4. Identify areas where the candidate's claims need verification
5. Frame everything diplomatically - you're seeking clarification, not making accusations

## WHAT TO LOOK FOR:

### **Employment Patterns**:
- Short tenures (< 1 year at multiple companies) - may indicate instability or performance issues
- Employment gaps (> 6 months) - need understanding of context
- Lateral moves without progression - may indicate lack of growth
- Job hopping without clear career direction

### **Skill Mismatches**:
- Critical required skills missing from resume
- Claimed skills without supporting project evidence
- Outdated technology stack for the role
- Over/under qualification for the seniority level

### **Experience Clarity**:
- Vague project descriptions (team size, personal contribution unclear)
- Use of "we" instead of "I" - hard to assess individual contribution
- Lack of measurable outcomes or impact
- Projects that don't demonstrate claimed expertise

### **Level Calibration**:
- Title inflation (senior title with junior experience)
- Underqualified for role requirements
- Overqualified (may be flight risk or unrealistic expectations)

### **Culture Fit Indicators**:
- Values misalignment based on company descriptions
- Work style preferences (remote vs. collaborative)
- Industry switches without clear rationale

## DIPLOMATIC FRAMING PRINCIPLES:
- **Assume positive intent**: Frame concerns as opportunities to learn more
- **Open-ended questions**: Avoid yes/no questions, encourage storytelling
- **Context matters**: Employment gap could be sabbatical, layoff, or family reasons
- **Verification, not accusation**: "Tell me more about..." not "Why did you..."
- **Growth opportunity**: Even concerns can reveal learning and adaptability

## SEVERITY CLASSIFICATION:
- **LOW**: Minor concerns, easy to clarify, unlikely to be deal-breakers
- **MEDIUM**: Notable gaps or patterns that require probing, could impact decision
- **HIGH**: Significant red flags that may be deal-breakers without strong explanation

## OUTPUT REQUIREMENTS:
Generate a RedFlagSet with 3-6 concerns:
- Order by severity (HIGH → MEDIUM → LOW)
- Be specific to THIS candidate and THIS role
- Provide context for why each concern matters
- Create diplomatic probe questions that encourage open discussion
- Specify what to listen for in responses"""


async def analyze_red_flags(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> list[RedFlag]:
    """Identify red flags and generate diplomatic probe questions using structured LLM output.
    
    Flow:
    1. Analyze resume patterns, employment history, skill gaps
    2. LLM generates RedFlagSet with 3-6 concerns
    3. Extract list of RedFlag objects
    4. Return ordered by severity
    """
    client = get_llm_client()

    # Extract resume details
    experience_level = structured_resume.get('experience_level', 'mid')
    years_exp = structured_resume.get('years_of_experience', 0)
    candidate_skills = structured_resume.get('skills', [])
    employment = structured_resume.get('employment_timeline', [])
    projects = structured_resume.get('projects', [])
    education = structured_resume.get('education', [])
    gaps = structured_resume.get('gaps', [])
    
    # Extract JD requirements
    required_skills = structured_jd.get('required_skills', [])
    seniority = structured_jd.get('seniority', 'mid')
    responsibilities = structured_jd.get('responsibilities', [])
    
    # Extract match insights
    overall_score = match_analysis.get('overall_match_score', 0)
    skill_gaps = match_analysis.get('skill_gaps', [])
    skill_matches = match_analysis.get('skill_matches', [])
    level_calibration = match_analysis.get('level_calibration', 'unknown')
    
    # Format employment for analysis
    employment_summary = "\n".join([
        f"  - {e.get('role', 'Unknown')} at {e.get('company', 'Unknown')}: {e.get('duration', 'Unknown')} ({e.get('start_date', '')} to {e.get('end_date', 'Present')})"
        for e in employment[:6]
    ]) if employment else "Not provided"
    
    # Format projects for analysis
    projects_summary = "\n".join([
        f"  - {p.get('name', 'Unnamed')}: {p.get('description', 'No description')[:80]}..."
        for p in projects[:5]
    ]) if projects else "Not provided"

    prompt = f"""## CANDIDATE PROFILE

### Basic Information
- **Experience Level**: {experience_level} ({years_exp} years)
- **Technical Skills**: {', '.join(candidate_skills[:25])}
- **Education**: {', '.join([f"{e.get('degree', '')} in {e.get('field', '')}" for e in education[:2]])}

### Employment History
{employment_summary}

### Notable Projects
{projects_summary}

### Identified Gaps/Concerns
{', '.join(gaps) if gaps else 'None automatically detected'}

---

## JOB REQUIREMENTS

- **Role**: {role_type.replace('_', ' ').title()}
- **Required Seniority**: {seniority}
- **Required Skills (Top 10)**: {', '.join(required_skills[:10])}
- **Key Responsibilities**: {'; '.join(responsibilities[:5])}

---

## MATCH ANALYSIS INSIGHTS

- **Overall Fit**: {overall_score:.1f}% ({level_calibration})
- **Skills Match**: {len(skill_matches)} skills aligned
- **Skill Gaps**: {', '.join(skill_gaps[:8]) if skill_gaps else 'None'}
- **Level Assessment**: {"Underqualified" if level_calibration == "underqualified" else "Overqualified" if level_calibration == "overqualified" else "Appropriately qualified" if level_calibration == "appropriate" else "Unclear"}

---

## YOUR TASK

Analyze this candidate and identify 3-6 potential concerns or areas requiring deeper investigation. Consider:

1. **Skill Gaps**: Are critical required skills missing? How significant?
2. **Employment Patterns**: Short tenures? Gaps? Unusual career progression?
3. **Experience vs. Requirements**: Does their {years_exp} years match {seniority} level expectations?
4. **Project Evidence**: Do their projects demonstrate the depth they claim?
5. **Contribution Clarity**: Can we clearly see THEIR individual impact vs. team effort?
6. **Level Calibration**: If {level_calibration}, what specific concerns does this raise?

**IMPORTANT**:
- Be specific to THIS candidate - reference actual employment/projects
- Prioritize concerns by severity (HIGH for potential deal-breakers)
- Frame diplomatically - you're seeking understanding, not accusing
- Provide actionable context for why each concern matters for THIS role
- Include specific indicators to listen for in their response

Generate the RedFlagSet NOW."""

    try:
        red_flag_set = await client.pydantic_generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_model=RedFlagSet,
            temperature=0.3,
            max_retries=3
        )
        return red_flag_set.red_flags
    except Exception as e:
        print(f"Error generating red flags with structured output: {e}")
        return _fallback_red_flags(skill_gaps, level_calibration, years_exp, seniority)


def _fallback_red_flags(
    skill_gaps: list[str], 
    level_calibration: str, 
    years_exp: int, 
    seniority: str
) -> list[RedFlag]:
    """Comprehensive fallback red flags if LLM fails."""
    flags = []
    
    # Check for skill gaps
    if skill_gaps:
        top_gaps = skill_gaps[:3]
        flags.append(RedFlag(
            concern=f"Missing key required skills: {', '.join(top_gaps)}",
            severity="medium" if len(skill_gaps) <= 2 else "high",
            probe_question=f"I noticed that {top_gaps[0]} isn't prominently featured in your background. Can you walk me through your experience with it and how you've applied it in your work?",
            what_to_listen_for="Listen for: concrete examples of using the technology, depth of understanding, willingness to learn if limited experience, adjacent skills that could transfer. Red flag if vague or purely theoretical knowledge.",
            context=f"This skill is listed as required for the role and appears in {len(skill_gaps)} identified gaps"
        ))
    
    # Check for level mismatch
    if level_calibration == "underqualified":
        flags.append(RedFlag(
            concern=f"Experience level ({years_exp} years) may be below {seniority} role requirements",
            severity="medium",
            probe_question=f"This role is typically suited for {seniority}-level candidates. What experience do you have that you feel prepares you for the increased responsibilities and technical depth required?",
            what_to_listen_for="Listen for: specific examples of complex projects, independent decision-making, mentoring others, handling ambiguous situations. Green flag: demonstrated growth trajectory and self-awareness about gaps.",
            context=f"Position requires {seniority} level but candidate has {years_exp} years experience"
        ))
    elif level_calibration == "overqualified":
        flags.append(RedFlag(
            concern="Candidate may be overqualified, potential flight risk or expectations mismatch",
            severity="low",
            probe_question="Given your background and experience level, what attracts you to this particular role? What are your expectations for growth and responsibilities?",
            what_to_listen_for="Listen for: genuine interest in the work, realistic expectations about scope, specific reasons for the role (not just 'any job'). Red flag: mentions this as a 'stepping stone' or seems primarily motivated by salary.",
            context="Candidate's experience level exceeds typical requirements for this position"
        ))
    
    # Generic career progression flag
    flags.append(RedFlag(
        concern="Career trajectory and individual contribution needs clarification",
        severity="low",
        probe_question="Walk me through your career progression - what were the key growth moments for you, and how did you measure your individual impact in team projects?",
        what_to_listen_for="Listen for: clear articulation of personal growth, specific metrics/outcomes they drove, use of 'I' statements showing individual contribution. Red flag: only team accomplishments, vague about personal role.",
        context="Need to verify hands-on experience depth and individual technical contributions"
    ))
    
    return flags[:4]  # Return top 4 flags

