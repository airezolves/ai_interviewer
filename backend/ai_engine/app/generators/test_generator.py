"""Practical Test Generator — skill-based technical assessments."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import PracticalTest, PracticalTestVariant, PracticalTestSet

SYSTEM_PROMPT = """You are a senior technical hiring manager with 15+ years of experience creating practical coding assessments.
Your task is to generate comprehensive, skill-based practical tests that will reveal a candidate's true technical competency.

## YOUR APPROACH:
1. Analyze the candidate's claimed technical skills and the JD's required skills
2. Select up to 8 CRITICAL technical skills that are:
   - Essential for the role (from JD requirements)
   - Claimed by the candidate (from their resume)
   - Testable through practical questions (not just theory)
3. For each skill, create 5 progressive questions:
   - 2 Junior level: Basic syntax, simple implementation, fundamental concepts
   - 2 Mid level: Practical application, optimization, real-world scenarios
   - 1 Senior level: Architecture, complex trade-offs, system design, advanced patterns

## QUESTION QUALITY CRITERIA:
- **Practical**: Real coding/implementation tasks, not theory questions
- **Specific**: Clear, unambiguous requirements
- **Testable**: Objective evaluation criteria
- **Progressive**: Junior → Mid → Senior shows depth progression
- **Relevant**: Matches actual job responsibilities
- **Time-bounded**: Junior (10-15 min), Mid (15-25 min), Senior (25-40 min)

## SKILL SELECTION PRIORITY:
1. Core languages/frameworks required by the role
2. Critical tools/technologies mentioned in JD
3. Skills candidate claims but needs verification
4. Domain-specific skills (e.g., ML algorithms for DS roles)

## OUTPUT REQUIREMENTS:
Generate a PracticalTestSet with 5-8 skill assessments, each containing exactly 5 questions (2 junior, 2 mid, 1 senior).
Total assessment should take 2-3 hours for a qualified candidate."""


async def generate_practical_test(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
) -> PracticalTest:
    """Generate skill-based practical assessments using structured LLM output.
    
    Flow:
    1. LLM generates PracticalTestSet (skill-based structure)
    2. Convert to PracticalTest (legacy format with variants) for backward compatibility
    3. Frontend parses variants to display skill-based structure
    """
    client = get_llm_client()

    # Extract candidate's technical skills
    candidate_skills = structured_resume.get('skills', [])
    projects = structured_resume.get('projects', [])
    experience_level = structured_resume.get('experience_level', 'mid')
    
    # Extract JD requirements
    required_skills = structured_jd.get('required_skills', [])
    nice_to_have = structured_jd.get('nice_to_have_skills', [])
    responsibilities = structured_jd.get('responsibilities', [])
    
    # Extract match insights
    skill_matches = match_analysis.get('skill_matches', [])
    skill_gaps = match_analysis.get('skill_gaps', [])

    prompt = f"""## ROLE CONTEXT
- **Position**: {role_type.replace('_', ' ').title()}
- **Candidate Experience Level**: {experience_level}
- **Required Seniority**: {structured_jd.get('seniority', 'mid')}

## CANDIDATE'S TECHNICAL SKILLS (from resume)
{', '.join(candidate_skills[:30])}

## JOB REQUIREMENTS
### Must-Have Skills:
{chr(10).join([f"  - {skill}" for skill in required_skills[:12]])}

### Nice-to-Have Skills:
{chr(10).join([f"  - {skill}" for skill in nice_to_have[:8]])}

### Key Responsibilities:
{chr(10).join([f"  - {resp}" for resp in responsibilities[:6]])}

## MATCH ANALYSIS
- **Skills Candidate Has**: {', '.join(skill_matches[:15])}
- **Skills Candidate Lacks**: {', '.join(skill_gaps[:10])}

## CANDIDATE'S PROJECT EXPERIENCE
{chr(10).join([f"  - {p.get('name', 'Project')}: Used {', '.join(p.get('technologies', [])[:5])}" for p in projects[:4]])}

---

## YOUR TASK

Select **5-8 critical technical skills** to assess. Prioritize:
1. Core programming languages/frameworks for this role
2. Skills both required by JD AND claimed by candidate (verify depth)
3. Critical tools mentioned in responsibilities
4. Skills with gaps (test if they have adjacent knowledge)

For each selected skill, generate 5 progressive practical questions:
- **2 Junior questions**: Basic implementation, syntax, simple use cases (10-15 min each)
- **2 Mid questions**: Real-world application, optimization, debugging (15-25 min each)
- **1 Senior question**: Architecture, complex scenarios, trade-offs, advanced patterns (25-40 min)

### EXAMPLE QUESTION PROGRESSION FOR "Python":

**Junior 1**: "Write a function that takes a list of numbers and returns only the even numbers. Handle edge cases like empty list."
- Tests: Basic syntax, list comprehension/filtering, edge case handling
- Time: 10 min

**Junior 2**: "Implement a class representing a Bank Account with deposit, withdraw, and check_balance methods. Include basic validation."
- Tests: OOP basics, methods, basic error handling
- Time: 15 min

**Mid 1**: "Given a CSV file with 1M rows, write code to find the top 10 most frequent values in a column efficiently. Optimize for memory and speed."
- Tests: File I/O, data processing, performance optimization, pandas/stdlib choice
- Time: 20 min

**Mid 2**: "Debug this code snippet that's causing a memory leak when processing large files. Identify the issue and fix it."
- Tests: Debugging skills, understanding of memory management, generator usage
- Time: 20 min

**Senior 1**: "Design a caching decorator that supports TTL (time-to-live), LRU eviction, and thread-safety. Implement the core logic."
- Tests: Advanced decorators, concurrency, data structures, design patterns
- Time: 35 min

---

Now generate a comprehensive PracticalTestSet with 5-8 skills relevant to this candidate and role."""

    try:
        test_set = await client.pydantic_generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_model=PracticalTestSet,
            temperature=0.3,
            max_retries=3
        )
        
        # Convert to legacy PracticalTest format for backward compatibility
        return _convert_to_legacy_format(test_set, role_type)
        
    except Exception as e:
        print(f"Error generating practical test with structured output: {e}")
        return _fallback_test(role_type)


def _convert_to_legacy_format(test_set: PracticalTestSet, role_type: str) -> PracticalTest:
    """Convert new skill-based format to legacy PracticalTest format."""
    # Create overview from all skills
    skills_tested = [assessment.skill_name for assessment in test_set.assessments]
    
    overview = f"""Comprehensive technical assessment covering {len(skills_tested)} critical skills: {', '.join(skills_tested)}.

This assessment contains {len(test_set.assessments)} skill-based sections with progressive difficulty levels.
Total time: {test_set.overall_time_estimate}.

{test_set.recommended_approach}"""
    
    # Create variants by aggregating questions by difficulty
    variants = []
    for difficulty_level in ['junior', 'mid', 'senior']:
        task_parts = []
        deliverables = []
        criteria = set()
        
        for assessment in test_set.assessments:
            level_questions = [q for q in assessment.questions if q.difficulty == difficulty_level]
            if level_questions:
                task_parts.append(f"\n**{assessment.skill_name}** ({len(level_questions)} questions):")
                for i, q in enumerate(level_questions, 1):
                    task_parts.append(f"{i}. {q.question}")
                    task_parts.append(f"   Time: {q.time_estimate} | Tests: {q.what_it_tests}")
                    criteria.update(q.evaluation_criteria)
        
        if task_parts:
            variants.append(PracticalTestVariant(
                difficulty=difficulty_level,
                task_description="\n".join(task_parts),
                dataset_scenario=f"Real-world scenarios testing {difficulty_level}-level competency",
                expected_deliverables=[f"Solutions for all {difficulty_level}-level questions", "Clean, well-commented code"],
                time_limit={
                    'junior': '45-60 minutes',
                    'mid': '60-90 minutes',
                    'senior': '60-90 minutes'
                }[difficulty_level],
                evaluation_criteria=list(criteria)[:8]
            ))
    
    return PracticalTest(
        title=f"{role_type.replace('_', ' ').title()} - Skill-Based Technical Assessment",
        overview=overview,
        variants=variants
    )


def _fallback_test(role_type: str) -> PracticalTest:
    """Comprehensive fallback test if LLM fails."""
    return PracticalTest(
        title=f"{role_type.replace('_', ' ').title()} Technical Assessment",
        overview="""Multi-skill practical assessment covering core technical competencies.
Complete as many questions as possible within the time limit.
Code quality, clarity, and correctness all matter.""",
        variants=[
            PracticalTestVariant(
                difficulty="junior",
                task_description="""**Section 1: Fundamentals**
1. Write a function to find the second largest number in a list
2. Implement a basic calculator class with add, subtract, multiply, divide methods
3. Parse a JSON file and extract specific nested fields
4. Write a function to check if a string is a valid email address""",
                dataset_scenario="Code challenges testing fundamental programming skills",
                expected_deliverables=["Working code for all functions", "Basic test cases"],
                time_limit="45 minutes",
                evaluation_criteria=["Code correctness", "Edge case handling", "Code clarity", "Basic error handling"]
            ),
            PracticalTestVariant(
                difficulty="mid",
                task_description="""**Section 2: Practical Application**
1. Optimize a slow function that processes a large dataset (provided)
2. Debug a code snippet with 3 subtle bugs
3. Implement a basic caching mechanism for expensive function calls
4. Write a script to aggregate data from multiple CSV files""",
                dataset_scenario="Real-world data processing and optimization scenarios",
                expected_deliverables=["Optimized solutions", "Performance comparisons", "Documentation"],
                time_limit="75 minutes",
                evaluation_criteria=["Performance optimization", "Debugging approach", "Design patterns", "Code maintainability"]
            ),
            PracticalTestVariant(
                difficulty="senior",
                task_description="""**Section 3: System Design & Architecture**
1. Design a rate-limiting system for an API (explain approach, data structures, trade-offs)
2. Implement a simple pub-sub event system
3. Design database schema for [role-relevant scenario]
4. Code review: Identify issues in provided code and suggest improvements""",
                dataset_scenario="Architecture and design challenges",
                expected_deliverables=["Design documents", "Implementation of key components", "Trade-off analysis"],
                time_limit="90 minutes",
                evaluation_criteria=["System design thinking", "Trade-off analysis", "Scalability considerations", "Code review quality"]
            )
        ]
    )
