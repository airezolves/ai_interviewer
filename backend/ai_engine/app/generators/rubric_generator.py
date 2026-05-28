"""Rubric Generator — weighted scoring criteria for objective evaluation."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import Rubric, RubricCriterion, RubricSet

SYSTEM_PROMPT = """You are a highly experienced senior hiring manager and interview trainer with 15+ years conducting structured interviews.
Your task is to create an objective, comprehensive scoring rubric that will help interviewers evaluate candidates consistently and fairly.

## YOUR APPROACH:
1. Analyze the job requirements and identify the CRITICAL skills and competencies needed
2. Create 6-8 evaluation criteria that comprehensively cover both technical and soft skills
3. Weight criteria based on importance to the role (most critical skills get higher weight)
4. Write clear, observable behavioral indicators for each score level
5. Ensure the rubric is practical and can be used during a live interview

## RUBRIC DESIGN PRINCIPLES:
- **Comprehensive**: Cover technical skills, soft skills, problem-solving, communication, and culture fit
- **Observable**: Score levels should describe specific behaviors/answers you can observe
- **Balanced**: Technical criteria 60-70%, soft skills 30-40%
- **Fair**: Criteria should be equally applicable regardless of background
- **Actionable**: Interviewers should know exactly what to listen for

## CRITERIA CATEGORIES TO CONSIDER:
- **Technical Depth**: Core technical skills required by the JD
- **Problem Solving**: Analytical thinking, debugging approach, handling ambiguity
- **System Design** (for mid/senior): Architecture thinking, scalability, trade-offs
- **Communication**: Clarity, conciseness, storytelling ability
- **Experience Depth**: Hands-on production experience vs. theoretical knowledge
- **Learning Agility**: Willingness to learn, handling new challenges
- **Collaboration**: Teamwork, handling conflict, cross-functional work
- **Culture Fit**: Alignment with company values and team dynamics

## SCORING GUIDANCE:
- **Score 1 (Poor)**: Fundamental gaps, cannot explain basics, red flags
- **Score 3 (Adequate)**: Meets minimum requirements, solid but not exceptional
- **Score 5 (Excellent)**: Exceeds expectations, demonstrates mastery and depth

## WEIGHT DISTRIBUTION GUIDELINES:
- Most critical skill: 25-30%
- Secondary critical skills: 15-20% each
- Soft skills: 10-15% each
- Total must equal 100%

## OUTPUT REQUIREMENTS:
Create a complete RubricSet with:
- 6-8 criteria that comprehensively evaluate THIS specific role
- Weights that reflect JD priorities
- Clear scoring_notes for using the rubric effectively"""


async def generate_rubric(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> Rubric:
    """Generate objective scoring rubric using structured LLM output.
    
    Flow:
    1. LLM generates RubricSet with detailed criteria
    2. Extract Rubric object
    3. Return with proper weights and scoring guidance
    """
    client = get_llm_client()

    # Extract JD details
    required_skills = structured_jd.get('required_skills', [])
    nice_to_have = structured_jd.get('nice_to_have_skills', [])
    responsibilities = structured_jd.get('responsibilities', [])
    seniority = structured_jd.get('seniority', 'mid')
    team_context = structured_jd.get('team_context', '')
    
    # Extract candidate details for calibration
    candidate_level = structured_resume.get('experience_level', 'mid')
    years_exp = structured_resume.get('years_of_experience', 0)
    candidate_skills = structured_resume.get('skills', [])
    
    # Extract match insights
    skill_gaps = match_analysis.get('skill_gaps', [])
    skill_matches = match_analysis.get('skill_matches', [])

    prompt = f"""## ROLE REQUIREMENTS ANALYSIS

### Position Details
- **Role**: {role_type.replace('_', ' ').title()}
- **Seniority Required**: {seniority} ({_seniority_years(seniority)})
- **Team Context**: {team_context or 'Not specified'}

### Must-Have Technical Skills (Top 10):
{chr(10).join([f"  {i+1}. {skill}" for i, skill in enumerate(required_skills[:10])])}

### Nice-to-Have Skills:
{', '.join(nice_to_have[:8])}

### Key Responsibilities:
{chr(10).join([f"  - {resp}" for resp in responsibilities[:8]])}

---

## CANDIDATE CALIBRATION

- **Candidate Level**: {candidate_level} ({years_exp} years experience)
- **Required Level**: {seniority}
- **Skills Alignment**: {len(skill_matches)} matching, {len(skill_gaps)} gaps
- **Critical Gaps to Assess**: {', '.join(skill_gaps[:5]) if skill_gaps else 'None'}

---

## YOUR TASK

Create a scoring rubric with 6-8 criteria that will help objectively evaluate whether this candidate can:

1. **Perform the core technical work**: Map the top 3-4 required skills to technical criteria
2. **Handle the responsibilities**: Create criteria based on key responsibilities
3. **Fit the seniority level**: Adjust expectations based on {seniority} level requirements
4. **Work effectively**: Include communication, collaboration, problem-solving criteria
5. **Learn and grow**: Assess learning agility, especially for skill gaps

**IMPORTANT WEIGHTINGS**:
- Top 2-3 most critical technical skills: 20-25% each
- Secondary technical/role-specific: 10-15% each
- Soft skills (communication, collaboration, problem-solving): 10-15% combined
- Must total exactly 100%

**OBSERVABLE BEHAVIORS**:
For each score level (1, 3, 5), describe SPECIFIC things you would hear/observe:
- Score 1: "Cannot explain basic concepts" or "Gives rambling, unclear answers"
- Score 3: "Can explain with examples" or "Provides clear, structured responses"
- Score 5: "Discusses trade-offs and edge cases" or "Exceptional clarity with compelling examples"

Create a comprehensive rubric that matches THIS specific role and candidate NOW."""

    try:
        rubric_set = await client.pydantic_generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_model=RubricSet,
            temperature=0.3,
            max_retries=3
        )
        return rubric_set.rubric
    except Exception as e:
        print(f"Error generating rubric with structured output: {e}")
        return _fallback_rubric(role_type, seniority, required_skills)


def _seniority_years(seniority: str) -> str:
    """Map seniority to typical years of experience."""
    mapping = {
        'junior': '0-2 years',
        'mid': '2-5 years',
        'senior': '5+ years'
    }
    return mapping.get(seniority, '2-5 years')


def _fallback_rubric(role_type: str, seniority: str, required_skills: list[str]) -> Rubric:
    """Comprehensive fallback rubric if LLM fails."""
    # Determine primary technical skill from requirements
    primary_skill = required_skills[0] if required_skills else "Technical Skills"
    secondary_skill = required_skills[1] if len(required_skills) > 1 else "Domain Knowledge"
    
    return Rubric(
        criteria=[
            RubricCriterion(
                name=f"{primary_skill} Proficiency",
                weight_pct=25,
                description=f"Depth of knowledge and hands-on experience with {primary_skill}",
                score_1="Cannot explain basic concepts, no practical experience evident",
                score_3="Solid understanding with clear examples from real work, can explain common patterns",
                score_5="Expert-level depth, discusses advanced topics, trade-offs, and optimization strategies"
            ),
            RubricCriterion(
                name=f"{secondary_skill}",
                weight_pct=20,
                description=f"Working knowledge of {secondary_skill} relevant to the role",
                score_1="Minimal or theoretical knowledge only, cannot provide examples",
                score_3="Practical experience, can describe how they've used it in projects",
                score_5="Deep expertise, can discuss best practices and advanced use cases"
            ),
            RubricCriterion(
                name="Problem Solving & Analytical Thinking",
                weight_pct=20,
                description="Structured approach to solving technical problems and handling complexity",
                score_1="No clear methodology, jumps to solutions without analysis",
                score_3="Systematic approach, breaks down problems, considers multiple solutions",
                score_5="Exceptional analytical skills, considers edge cases, optimal solutions, and trade-offs"
            ),
            RubricCriterion(
                name="Communication & Clarity",
                weight_pct=15,
                description="Ability to explain technical concepts clearly and concisely",
                score_1="Unclear, rambling explanations, cannot simplify complex topics",
                score_3="Clear and structured communication, explains concepts well",
                score_5="Exceptional clarity, uses analogies effectively, adapts explanation to audience"
            ),
            RubricCriterion(
                name="Production Experience Depth",
                weight_pct=10,
                description="Real-world experience building and maintaining production systems",
                score_1="Mostly academic or toy projects, no production exposure",
                score_3="Has worked on production systems, understands deployment and monitoring",
                score_5="Deep production experience, discusses scalability, reliability, and operational concerns"
            ),
            RubricCriterion(
                name="Learning Agility & Growth Mindset",
                weight_pct=10,
                description="Ability to learn new technologies and adapt to changing requirements",
                score_1="Defensive about gaps, rigid thinking, unwilling to learn",
                score_3="Open to feedback, demonstrates past learning experiences",
                score_5="Proactively seeks growth, learns quickly, thrives on new challenges"
            ),
        ],
        pass_threshold=3.0 if seniority == 'junior' else 3.2 if seniority == 'mid' else 3.5,
        total_weight=100,
        scoring_notes=f"For {seniority}-level candidates, expect: {'foundational understanding and eagerness to learn' if seniority == 'junior' else 'solid practical experience and independent execution' if seniority == 'mid' else 'deep expertise and leadership in technical decisions'}. Score based on examples and depth of understanding, not just theoretical knowledge."
    )

