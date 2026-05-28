"""Flow Guide Generator — minute-by-minute interview structure and execution plan."""

from backend.ai_engine.app.generators.llm_client import get_llm_client
from shared.schemas.kit import FlowSection, FlowGuide

SYSTEM_PROMPT = """You are a highly experienced interview trainer and senior hiring manager who has conducted thousands of technical interviews.
Your task is to create a practical, minute-by-minute interview flow guide that helps interviewers run effective, structured interviews.

## YOUR APPROACH:
1. Structure a 60-minute interview into 5-7 logical sections
2. Allocate time based on interview priorities (technical depth gets more time)
3. Map specific question indices to each section for smooth flow
4. Provide practical interviewer notes and tips for each section
5. Build rapport early, then progressively deepen technical assessment

## PROVEN INTERVIEW STRUCTURE (60 minutes total):

### **1. Introduction & Rapport Building (5 minutes)**
- Welcome and put candidate at ease
- Set agenda and explain interview format
- Brief overview of role and company
- **Goal**: Create comfortable atmosphere, reduce nervousness

### **2. Background & Career Journey (8-10 minutes)**
- Walk through resume and recent experience
- Understand motivations and career decisions
- Ask 1-2 behavioral questions about past experiences
- **Goal**: Understand context and assess communication skills

### **3. Technical Deep Dive (20-25 minutes)**
- Core technical questions based on required skills
- Probe depth with follow-up questions
- Assess hands-on experience vs. theoretical knowledge
- **Goal**: Verify technical competency in critical areas

### **4. Problem Solving & System Design (10-15 minutes)**
- Practical scenarios or architecture discussions
- Observe approach to ambiguous problems
- Assess ability to make trade-offs
- **Goal**: Evaluate analytical thinking and design skills

### **5. Red Flags & Gap Probing (5-8 minutes)**
- Diplomatically investigate concerns
- Clarify resume gaps or skill mismatches
- Give candidate chance to address potential issues
- **Goal**: Verify assumptions and clear up concerns

### **6. Candidate Questions & Close (7-10 minutes)**
- Answer candidate's questions
- Gauge their interest and understanding
- Explain next steps
- **Goal**: Sell the role, assess candidate interest

## TIME MANAGEMENT PRINCIPLES:
- Start on time, respect the 60-minute limit
- Front-load critical technical assessment (first 30 min)
- Be flexible - can extend good discussions by cutting less critical sections
- Leave adequate time for candidate questions (shows respect)
- Build in 2-3 min buffer for transitions

## QUESTION MAPPING STRATEGY:
- Map question indices (0-based) to appropriate sections
- **Behavioral questions** → Background section
- **Core technical questions** → Technical Deep Dive
- **System design questions** → Problem Solving section
- **Gap verification questions** → Red Flags section
- Aim for 2-4 questions per section (varies by section purpose)

## INTERVIEWER NOTES GUIDELINES:
- Provide actionable tips for each section
- Mention what to watch for or common pitfalls
- Suggest how to adapt based on candidate responses
- Include reminders about fairness and consistency

## OUTPUT REQUIREMENTS:
Generate a FlowGuide with:
- 5-7 sections covering the full 60 minutes
- Total duration must equal 60 minutes
- Specific question indices mapped to each section
- Practical interviewer_notes for each section
- Helpful preparation_notes for the interviewer"""


async def generate_flow_guide(
    structured_resume: dict,
    structured_jd: dict,
    match_analysis: dict,
    role_type: str,
    questions: list[dict] | None = None,  # NEW: Actual questions for intelligent mapping
) -> list[FlowSection]:
    """Generate minute-by-minute interview flow guide using structured LLM output.
    
    Flow:
    1. Analyze candidate level and role requirements
    2. Analyze generated questions (if provided) to map categories to sections
    3. LLM generates FlowGuide with 5-7 sections
    4. Extract list of FlowSection objects
    5. Return sections in chronological order
    """
    client = get_llm_client()

    # Extract candidate details
    experience_level = structured_resume.get('experience_level', 'mid')
    years_exp = structured_resume.get('years_of_experience', 0)
    
    # Extract JD requirements
    seniority = structured_jd.get('seniority', 'mid')
    required_skills = structured_jd.get('required_skills', [])
    responsibilities = structured_jd.get('responsibilities', [])
    
    # Extract match insights
    skill_gaps = match_analysis.get('skill_gaps', [])
    level_calibration = match_analysis.get('level_calibration', 'unknown')
    
    # Analyze questions for intelligent mapping
    question_summary = ""
    if questions:
        # Group questions by category
        categories = {}
        for idx, q in enumerate(questions):
            cat = q.get('category', 'technical_depth')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(idx)
        
        question_summary = f"""
### Generated Question Bank ({len(questions)} questions)

Question indices by category:
- **Behavioral**: {categories.get('behavioral', [])} ({len(categories.get('behavioral', []))} questions)
- **Technical Depth**: {categories.get('technical_depth', [])} ({len(categories.get('technical_depth', []))} questions)
- **System Design**: {categories.get('system_design', [])} ({len(categories.get('system_design', []))} questions)
- **Problem Solving**: {categories.get('problem_solving', [])} ({len(categories.get('problem_solving', []))} questions)
- **Domain Knowledge**: {categories.get('domain_knowledge', [])} ({len(categories.get('domain_knowledge', []))} questions)
- **Gap Verification**: {categories.get('gap_verification', [])} ({len(categories.get('gap_verification', []))} questions)

**IMPORTANT**: Map these ACTUAL question indices to appropriate sections. 
Use behavioral questions in Background section, technical questions in Deep Dive, etc."""
    else:
        question_summary = """
### Question Bank Status
Questions not yet generated. Create a generic mapping assuming:
- Questions 0-2: Behavioral/Background
- Questions 3-10: Technical Depth
- Questions 11-14: Problem Solving/System Design
- Questions 15-17: Gap Verification"""

    prompt = f"""## INTERVIEW SETUP

### Role & Candidate Overview
- **Position**: {role_type.replace('_', ' ').title()} ({seniority} level)
- **Candidate**: {experience_level} level, {years_exp} years experience
- **Level Match**: {level_calibration}

### Interview Focus Areas
- **Top 3 Skills to Assess**: {', '.join(required_skills[:3])}
- **Key Responsibilities to Discuss**: {'; '.join(responsibilities[:3])}
- **Skill Gaps to Probe**: {', '.join(skill_gaps[:3]) if skill_gaps else 'None identified'}

### Interview Context
- **Duration**: 60 minutes total
- **Format**: Structured technical interview with behavioral component

{question_summary}

---

## YOUR TASK

Create a practical 60-minute interview flow that:

1. **Builds rapport first** (5 min) - Warm welcome, set agenda, make candidate comfortable
   - No questions mapped (just introduction)

2. **Assesses background** (8-10 min) - Career journey, key experiences, behavioral questions
   - Map BEHAVIORAL question indices from the bank above
   - Focus on understanding context and communication skills

3. **Deep-dives technically** (20-25 min) - Core technical skills, hands-on experience
   - Map TECHNICAL DEPTH question indices from the bank above
   - Allocate more time here - this is the critical assessment
   - For {seniority} level: {"Assess fundamentals and learning potential" if seniority == "junior" else "Verify independent execution and depth" if seniority == "mid" else "Evaluate expertise, architecture thinking, and leadership"}

4. **Tests problem-solving** (10-15 min) - Practical scenarios, system design, analytical thinking
   - Map SYSTEM DESIGN and PROBLEM SOLVING question indices from the bank above
   - Observe approach to ambiguous problems

5. **Probes concerns** (5-8 min) - Address skill gaps, red flags, clarifications
   - Map GAP VERIFICATION question indices from the bank above
   - Be diplomatic but thorough

6. **Candidate questions & close** (7-10 min) - Answer questions, gauge interest, next steps
   - No questions mapped (candidate-driven discussion)
   - Sell the role, explain process

**IMPORTANT**: Use the ACTUAL question indices provided above. Match question categories to appropriate interview sections.

**INTERVIEWER NOTES** for each section should include:
- What to watch for
- How to adapt based on candidate responses
- Common pitfalls to avoid
- Tips for getting the best signal

**PREPARATION NOTES** should cover:
- Pre-interview preparation steps
- Materials to review
- Mindset and fairness reminders

Generate the FlowGuide NOW with {seniority}-appropriate depth and pacing."""

    try:
        flow_guide = await client.pydantic_generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            response_model=FlowGuide,
            temperature=0.3,
            max_retries=3
        )
        return flow_guide.sections
    except Exception as e:
        print(f"Error generating flow guide with structured output: {e}")
        return _fallback_flow(role_type, seniority, skill_gaps)


def _fallback_flow(role_type: str, seniority: str, skill_gaps: list[str]) -> list[FlowSection]:
    """Comprehensive fallback flow guide if LLM fails."""
    
    # Adjust expectations based on seniority
    technical_focus = {
        'junior': 'Focus on fundamentals, learning ability, and potential',
        'mid': 'Verify independent execution, practical experience, and problem-solving',
        'senior': 'Assess deep expertise, architectural thinking, and technical leadership'
    }.get(seniority, 'Assess technical competency and hands-on experience')
    
    return [
        FlowSection(
            section="Introduction & Rapport Building",
            duration_minutes=5,
            activities=[
                "Welcome candidate warmly and thank them for their time",
                "Introduce yourself and briefly explain the interview format",
                "Set agenda: 'We'll discuss your background, dive into some technical topics, and leave time for your questions'",
                "Ask: 'How are you doing today?' or 'Did you find the office okay?'",
                "Put candidate at ease before diving into assessment"
            ],
            questions_mapped=[],
            interviewer_notes="Goal: Create a comfortable atmosphere. If candidate seems nervous, spend an extra minute on small talk. Your demeanor sets the tone - be warm but professional. Remind them it's a conversation, not an interrogation."
        ),
        FlowSection(
            section="Background & Career Journey",
            duration_minutes=10,
            activities=[
                "Ask candidate to walk through their career progression",
                "Understand motivations for role transitions",
                "Probe recent projects and contributions",
                "Ask 1-2 behavioral questions about past experiences",
                "Assess communication clarity and self-awareness"
            ],
            questions_mapped=[0, 1],
            interviewer_notes="Watch for: Clear communication, genuine passion for the work, self-awareness about strengths/gaps. Listen for 'I' vs 'we' to gauge individual contribution. Good time to build rapport while gathering context for later technical questions."
        ),
        FlowSection(
            section="Technical Deep Dive",
            duration_minutes=24,
            activities=[
                f"Assess core technical skills: {skill_gaps[0] if skill_gaps else 'primary technology'}",
                "Ask hands-on questions about real work experience",
                "Use follow-up probes to verify depth vs. surface knowledge",
                f"{technical_focus}",
                "Look for evidence of production experience, not just theory"
            ],
            questions_mapped=[2, 3, 4, 5, 6, 7],
            interviewer_notes=f"CRITICAL SECTION - This is your main technical assessment. For {seniority}: {technical_focus}. If answer is too brief, ask 'Can you tell me more about how you implemented that?' If too theoretical, ask 'What production challenges did you face?' Take notes on specific examples."
        ),
        FlowSection(
            section="Problem Solving & System Design",
            duration_minutes=12,
            activities=[
                "Present a practical scenario or design problem",
                "Observe approach to ambiguous situations",
                "Assess ability to make trade-offs and justify decisions",
                "Evaluate architectural thinking (for mid/senior levels)",
                "Look for structured problem-solving methodology"
            ],
            questions_mapped=[8, 9, 10],
            interviewer_notes="Don't jump to solutions - observe their PROCESS. Good candidates ask clarifying questions, think out loud, consider multiple approaches. For system design: look for scalability considerations, failure modes, monitoring. It's okay if they don't have perfect answers - you're evaluating thinking, not memorization."
        ),
        FlowSection(
            section="Gap Verification & Red Flags",
            duration_minutes=6,
            activities=[
                f"Diplomatically probe identified gaps: {', '.join(skill_gaps[:2]) if skill_gaps else 'skill alignment'}",
                "Ask about any resume concerns or unclear areas",
                "Give candidate opportunity to address potential issues",
                "Verify individual contributions in team projects",
                "Clarify any timeline gaps or short tenures"
            ],
            questions_mapped=[11, 12],
            interviewer_notes="BE DIPLOMATIC. Frame as 'I'd love to learn more about...' not 'I'm concerned that...'. Listen for honesty, self-awareness, and learning mindset. Red flags: defensive responses, blaming others, vague about personal contribution. Green flags: acknowledges gaps honestly, shows willingness to learn."
        ),
        FlowSection(
            section="Candidate Questions & Closing",
            duration_minutes=10,
            activities=[
                "Invite candidate's questions - this is important!",
                "Answer thoughtfully and honestly about role, team, culture",
                "Gauge candidate interest through their questions",
                "Explain next steps and timeline clearly",
                "Thank them and leave positive impression regardless of outcome"
            ],
            questions_mapped=[],
            interviewer_notes="Quality of questions tells you a lot - thoughtful questions show genuine interest. If they ask about growth, impact, team dynamics = good sign. If only about salary, benefits = potential red flag. Be honest about challenges - selling false picture helps no one. End warmly - they could be your colleague!"
        ),
    ]

