"""Question Generator — tailored interview questions with model answers."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import Question, QuestionSet

SYSTEM_PROMPT = """You are a highly experienced senior technical interviewer with 15+ years of experience hiring for technical roles.
Your task is to generate a comprehensive, personalized interview question bank that will help thoroughly evaluate a candidate.

## YOUR APPROACH:
1. Deeply analyze the candidate's resume - their actual projects, technologies used, employment timeline, and claimed expertise
2. Study the job description requirements - both must-have and nice-to-have skills
3. Review the match analysis to identify strengths to verify and gaps to probe
4. Design questions that reveal true competency vs. surface-level knowledge
5. Create follow-ups that expose depth of understanding and real-world application

## QUESTION CATEGORIES (generate 15-20 questions total):
- **technical_depth** (6-8 questions): Verify claimed technical skills with hands-on scenarios from their actual projects
- **behavioral** (3-4 questions): Understand past behavior, decision-making, collaboration, and conflict resolution
- **system_design** (2-3 questions): Assess architecture thinking, scalability, and trade-off analysis at appropriate seniority
- **domain_knowledge** (1-2 questions): Test industry-specific knowledge relevant to the role
- **problem_solving** (2-3 questions): Evaluate analytical thinking, debugging approach, and handling ambiguity
- **gap_verification** (2-3 questions): Tactfully probe identified skill gaps to assess learning ability and honesty

## QUESTION QUALITY CRITERIA:
- **Specific to candidate**: Reference their actual projects, technologies, or employment history
- **Probing**: Questions should reveal depth, not just memorized answers
- **Practical**: Focus on real-world scenarios they'll face in the role
- **Fair**: Match difficulty to the required seniority level
- **Progressive**: Start with their strengths, then probe gaps and growth areas

## OUTPUT REQUIREMENTS:
Generate a comprehensive QuestionSet with 15-20 well-crafted questions that will give the interviewer a complete picture of the candidate's capabilities."""


async def generate_questions(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> list[Question]:
    """Generate tailored interview questions using structured LLM output."""
    client = get_llm_client()

    # Extract detailed context from resume
    candidate_skills = structured_resume.get('skills', [])
    projects = structured_resume.get('projects', [])
    employment = structured_resume.get('employment_timeline', [])
    experience_level = structured_resume.get('experience_level', 'mid')
    years_experience = structured_resume.get('years_of_experience', 0)
    education = structured_resume.get('education', [])
    gaps = structured_resume.get('gaps', [])
    
    # Format projects for context
    projects_summary = "\n".join([
        f"  - {p.get('name', 'Unknown')}: {p.get('description', '')[:100]}... (Tech: {', '.join(p.get('technologies', [])[:5])})"
        for p in projects[:5]
    ])
    
    # Format employment for context
    employment_summary = "\n".join([
        f"  - {e.get('role', 'Unknown')} at {e.get('company', 'Unknown')} ({e.get('duration', 'Unknown')})"
        for e in employment[:3]
    ])

    prompt = f"""## CANDIDATE PROFILE ANALYSIS

### Basic Information
- **Role Applied For**: {role_type.replace('_', ' ').title()}
- **Experience Level**: {experience_level} ({years_experience} years)
- **Education**: {', '.join([e.get('degree', '') for e in education[:2]])}

### Employment History
{employment_summary}

### Key Technical Skills (from resume)
{', '.join(candidate_skills[:25])}

### Notable Projects
{projects_summary}

### Identified Concerns
{', '.join(gaps) if gaps else 'None identified'}

---

## JOB REQUIREMENTS ANALYSIS

### Position Details
- **Seniority Required**: {structured_jd.get('seniority', 'mid')}
- **Team Context**: {structured_jd.get('team_context', 'Not specified')}

### Required Skills (Must-Have)
{chr(10).join([f"  - {skill}" for skill in structured_jd.get('required_skills', [])[:10]])}

### Nice-to-Have Skills
{chr(10).join([f"  - {skill}" for skill in structured_jd.get('nice_to_have_skills', [])[:8]])}

### Key Responsibilities
{chr(10).join([f"  - {resp}" for resp in structured_jd.get('responsibilities', [])[:8]])}

---

## MATCH ANALYSIS INSIGHTS

### Overall Fit: {match_analysis.get('overall_match_score', 0):.1f}/100
**Calibration**: {match_analysis.get('level_calibration', 'unknown')}

### Strengths (Skills Present)
{', '.join(match_analysis.get('skill_matches', [])[:10])}

### Gaps (Skills Missing)
{', '.join(match_analysis.get('skill_gaps', [])[:10])}

### Experience Assessment
{match_analysis.get('experience_fit', 'Not assessed')}

---

## YOUR TASK

Based on this comprehensive analysis, generate 15-20 interview questions that will:

1. **Verify Technical Claims**: Create hands-on questions about technologies they've listed, referencing their actual projects
2. **Probe Depth**: Don't just ask definitions - ask about real challenges, trade-offs, and decisions they made
3. **Address Gaps**: Tactfully explore missing skills to see if they have adjacent experience or learning ability
4. **Assess Seniority**: Questions should match the {structured_jd.get('seniority', 'mid')} level required
5. **Explore Behavior**: Understand how they work in teams, handle pressure, resolve conflicts
6. **Test Problem-Solving**: Present realistic scenarios they'll face in this role

**IMPORTANT**: 
- Reference SPECIFIC projects from their resume (e.g., "In your {projects[0].get('name', 'project') if projects else 'previous work'}...")
- Use actual technologies they claim (e.g., "You mentioned using {candidate_skills[0] if candidate_skills else 'Python'}...")
- Tailor difficulty to their experience level
- Include a relevance_rationale explaining why each question matters for THIS candidate

Generate a comprehensive QuestionSet now."""

    try:
        question_set = await client.pydantic_generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_model=QuestionSet,
            temperature=0.3,  # Lower temperature for more consistent structure
            max_retries=3
        )
        return question_set.questions
    except Exception as e:
        print(f"Error generating questions with structured output: {e}")
        return _fallback_questions(role_type)


def _fallback_questions(role_type: str) -> list[Question]:
    """Comprehensive fallback questions if LLM fails."""
    return [
        Question(
            question="Walk me through your most challenging technical project from start to finish.",
            category="behavioral",
            what_it_tests="Communication, problem-solving, end-to-end thinking, impact orientation",
            model_answer="A strong answer covers: problem context, technical approach, challenges faced, solutions implemented, measurable outcomes, and lessons learned. Shows ownership and impact.",
            follow_up_probes=[
                "What was the biggest technical challenge and how did you overcome it?",
                "How did you measure success? What were the business or user outcomes?",
                "If you could redo this project, what would you do differently?",
                "How did you handle disagreements or trade-offs during the project?"
            ],
            difficulty="medium",
            relevance_rationale="Assesses end-to-end project ownership, technical depth, and business impact"
        ),
        Question(
            question="Describe a situation where you had to learn a new technology or framework quickly to meet a deadline.",
            category="behavioral",
            what_it_tests="Learning agility, adaptability, time management, pressure handling",
            model_answer="Strong answer shows systematic learning approach, resourcefulness, asking for help when needed, and successfully delivering despite tight timeline.",
            follow_up_probes=[
                "What resources did you use to learn?",
                "How did you balance learning with delivery?",
                "What mistakes did you make and how did you recover?"
            ],
            difficulty="easy",
            relevance_rationale="Evaluates ability to adapt and learn - critical for fast-paced environments"
        ),
        Question(
            question="Explain the trade-offs between different approaches you've used to solve a specific technical problem in your experience.",
            category="technical_depth",
            what_it_tests="Deep technical understanding, trade-off analysis, decision-making",
            model_answer="Strong answer compares 2-3 approaches with specific criteria: performance, maintainability, scalability, cost. Explains why the chosen approach was optimal for that context.",
            follow_up_probes=[
                "What metrics did you use to evaluate these approaches?",
                "How would your decision change if [constraint] changed?",
                "What would you monitor in production to validate your choice?"
            ],
            difficulty="hard",
            relevance_rationale="Tests ability to think critically about technical decisions beyond implementation"
        ),
        Question(
            question="Tell me about a time when you had to debug a particularly difficult issue. How did you approach it?",
            category="problem_solving",
            what_it_tests="Debugging methodology, systematic thinking, persistence, root cause analysis",
            model_answer="Describes systematic approach: reproducing the issue, forming hypotheses, isolating variables, using debugging tools, finding root cause (not just symptoms), and preventing recurrence.",
            follow_up_probes=[
                "What tools did you use for debugging?",
                "How long did it take and what was your thought process?",
                "How did you prevent similar issues in the future?"
            ],
            difficulty="medium",
            relevance_rationale="Reveals problem-solving approach and ability to handle ambiguous technical challenges"
        ),
        Question(
            question="How do you ensure code quality and maintainability in your projects?",
            category="technical_depth",
            what_it_tests="Software engineering best practices, quality mindset, team collaboration",
            model_answer="Mentions practices like: code reviews, testing (unit, integration), documentation, design patterns, CI/CD, linting, and clear naming. Shows balance between pragmatism and perfection.",
            follow_up_probes=[
                "How do you handle code review feedback?",
                "What's your testing philosophy?",
                "Give an example of technical debt you've addressed"
            ],
            difficulty="easy",
            relevance_rationale="Assesses software craftsmanship and professional maturity"
        ),
        Question(
            question="Describe a situation where you disagreed with a team member or manager on a technical decision. How did you handle it?",
            category="behavioral",
            what_it_tests="Communication, conflict resolution, technical advocacy, collaboration",
            model_answer="Shows ability to articulate technical opinions with data/evidence, listen to others' perspectives, find common ground, and commit to team decisions even when not fully aligned.",
            follow_up_probes=[
                "What was the outcome?",
                "How did you maintain the relationship?",
                "In hindsight, who was right?"
            ],
            difficulty="medium",
            relevance_rationale="Tests collaboration skills and ability to handle technical disagreements professionally"
        ),
        Question(
            question="Walk me through how you would design a system to handle [relevant use case for the role].",
            category="system_design",
            what_it_tests="Architecture thinking, scalability, trade-offs, practical system design",
            model_answer="Asks clarifying questions, defines requirements, proposes high-level architecture, discusses data flow, identifies bottlenecks, suggests scaling strategies, mentions monitoring and failure handling.",
            follow_up_probes=[
                "How would you handle a 10x increase in traffic?",
                "What could go wrong and how would you mitigate it?",
                "How would you monitor this system in production?"
            ],
            difficulty="hard",
            relevance_rationale="Evaluates ability to design scalable systems at appropriate complexity level"
        ),
        Question(
            question="Tell me about a time you made a mistake that impacted users or the production system. What happened and what did you learn?",
            category="behavioral",
            what_it_tests="Accountability, learning from failure, incident response, honesty",
            model_answer="Shows ownership of mistake, describes immediate response to mitigate impact, explains root cause, details preventive measures implemented, and demonstrates growth mindset.",
            follow_up_probes=[
                "How did you communicate with stakeholders?",
                "What systems did you put in place to prevent this?",
                "How has this changed your approach?"
            ],
            difficulty="medium",
            relevance_rationale="Tests maturity, accountability, and ability to learn from failures"
        ),
    ]
