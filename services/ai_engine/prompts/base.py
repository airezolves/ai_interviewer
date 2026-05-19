"""Base prompt utilities."""

ROLE_TYPES = [
    "data_scientist",
    "ml_engineer",
    "data_analyst",
    "data_engineer",
    "analytics_engineer",
    "software_engineer",
    "backend_engineer",
    "frontend_engineer",
    "fullstack_engineer",
]


def build_context_block(jd_analysis: dict, resume_data: dict) -> str:
    """Build the common context block used in all generation prompts."""
    return f"""
=== JOB DESCRIPTION ANALYSIS ===
Role: {jd_analysis.get('role_title', 'N/A')}
Seniority: {jd_analysis.get('seniority_level', 'N/A')}
Required Skills: {', '.join(jd_analysis.get('required_skills', []))}
Nice-to-Have Skills: {', '.join(jd_analysis.get('nice_to_haves', []))}
Key Responsibilities: {', '.join(jd_analysis.get('responsibilities', [])[:5])}
Team Context: {jd_analysis.get('team_context', 'N/A')}

=== CANDIDATE PROFILE ===
Name: {resume_data.get('name', 'N/A')}
Current Role: {resume_data.get('current_role', 'N/A')}
Experience: {resume_data.get('total_experience_years', 'N/A')} years
Technical Skills: {', '.join(resume_data.get('technical_skills', [])[:15])}
Key Strengths: {', '.join(resume_data.get('strengths', []))}
Potential Concerns: {', '.join(resume_data.get('concerns', []))}
"""
