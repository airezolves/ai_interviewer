"""Unit tests for AI Engine service."""

import pytest
from services.ai_engine.prompts.base import build_context_block, ROLE_TYPES
from services.ai_engine.prompts.questions import get_questions_prompt


class TestPromptBase:
    """Test prompt utility functions."""

    def test_role_types_defined(self):
        assert len(ROLE_TYPES) > 0
        assert "data_scientist" in ROLE_TYPES

    def test_build_context_block(self):
        jd_analysis = {
            "role_title": "Senior Data Scientist",
            "seniority_level": "senior",
            "required_skills": ["Python", "SQL", "ML"],
            "nice_to_haves": ["Spark"],
            "responsibilities": ["Build models"],
            "team_context": "Data team of 5",
        }
        resume_data = {
            "name": "Test User",
            "current_role": "Data Scientist",
            "total_experience_years": 5,
            "technical_skills": ["Python", "SQL"],
            "strengths": ["Strong ML skills"],
            "concerns": ["No leadership experience"],
        }

        context = build_context_block(jd_analysis, resume_data)

        assert "Senior Data Scientist" in context
        assert "Python" in context
        assert "Test User" in context
        assert "5" in context

    def test_questions_prompt_contains_role(self):
        jd_analysis = {
            "role_title": "ML Engineer",
            "seniority_level": "mid",
            "required_skills": ["PyTorch"],
            "nice_to_haves": [],
            "responsibilities": [],
            "team_context": "",
        }
        resume_data = {
            "name": "Candidate",
            "current_role": "SWE",
            "total_experience_years": 3,
            "technical_skills": ["Python"],
            "strengths": [],
            "concerns": [],
        }

        prompt = get_questions_prompt(jd_analysis, resume_data, "ml_engineer")
        assert "Ml Engineer" in prompt
        assert "ML Engineer" in prompt or "Ml Engineer" in prompt
