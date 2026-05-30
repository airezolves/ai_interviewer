"""
Skill Manager - Load SKILL.md files at startup, apply at request time.

Skills are domain-knowledge documents (SKILL.md) that inject context into the
planner prompt so the LLM knows exactly how to use tools for a given domain.

Lifecycle:
  1. load_skills() - reads all SKILL.md from orchestrator/skills/* into memory
  2. intent_analysis picks a matched_skill name (e.g. "blast-radius")
  3. apply_skill(name) - returns the prompt injection text for the planner

Skills do NOT call tools or loop - they only provide domain context.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("runtime.skill_manager")

# Default skills directory (relative to this file)
_DEFAULT_SKILLS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skills",
)


class SkillDefinition:
    """A loaded skill - name, description, and full markdown body."""

    __slots__ = ("name", "description", "body")

    def __init__(self, name: str, description: str, body: str) -> None:
        self.name = name
        self.description = description
        self.body = body

    def __repr__(self) -> str:
        return f"Skill({self.name!r}, {len(self.body)} chars)"


def _parse_skill_md(path: str) -> Optional[SkillDefinition]:
    """
    Parse a SKILL.md file.

    Supports two formats:
    - YAML frontmatter (---name/description---) + markdown body
    - Pure YAML (starts with 'skills:') - treated as body with folder name
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return None

    folder_name = os.path.basename(os.path.dirname(path))

    # Format 1: YAML frontmatter delimited by ---
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].strip()

            name = folder_name
            description = ""
            for line in frontmatter.splitlines():
                line = line.strip()
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip('"').strip("'")

            return SkillDefinition(name=name, description=description, body=body)

    # Format 2: Pure YAML (sub-skills list) - use entire content as body
    name = folder_name
    description = f"Domain knowledge for {folder_name}"
    return SkillDefinition(name=name, description=description, body=text)


class SkillManager:
    """
    Manages skill loading and application.

    - At startup / first access: loads all SKILL.md files from skills/ directory
    - At request time: apply_skill() returns the prompt injection
    """

    def __init__(self, skills_dir: str = _DEFAULT_SKILLS_DIR) -> None:
        self._skills_dir = skills_dir
        self._skills: Dict[str, SkillDefinition] = {}
        self._loaded = False

    def load_skills(self) -> None:
        """Load all SKILL.md files from the skills directory into memory."""
        if self._loaded:
            return

        skills_path = Path(self._skills_dir)
        if not skills_path.is_dir():
            logger.warning("Skills directory not found: %s", self._skills_dir)
            self._loaded = True
            return

        count = 0
        for child in sorted(skills_path.iterdir()):
            if not child.is_dir():
                continue
            skill_file = child / "SKILL.md"
            if not skill_file.exists():
                continue

            skill = _parse_skill_md(str(skill_file))
            if skill:
                self._skills[skill.name] = skill
                count += 1
                logger.debug("Loaded skill: %s (%d chars)", skill.name, len(skill.body))

        self._loaded = True
        logger.info(
            "Loaded %d skills from %s: [%s]",
            count,
            self._skills_dir,
            ", ".join(sorted(self._skills.keys())),
        )

    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        """Look up a skill by name."""
        self.load_skills()
        return self._skills.get(name)

    def list_skills(self) -> List[SkillDefinition]:
        """Return all loaded skills."""
        self.load_skills()
        return list(self._skills.values())

    def get_skill_names(self) -> List[str]:
        """Return all loaded skill names."""
        self.load_skills()
        return sorted(self._skills.keys())

    def get_skill_descriptions(self) -> str:
        """Return skill names + descriptions for the planner prompt."""
        self.load_skills()
        if not self._skills:
            return "No skills available."
        lines = []
        for s in sorted(self._skills.values(), key=lambda x: x.name):
            lines.append(f"- **{s.name}**: {s.description[:200]}")
        return "\n".join(lines)

    def apply_skill(self, skill_name: str) -> Dict[str, Any]:
        """
        Apply a skill - returns the prompt injection for the planner.

        Returns dict with:
        - prompt_addition: full skill body to inject into the planner system prompt
        - skill_name: the resolved skill name
        - found: whether the skill was found
        """
        self.load_skills()
        skill = self._skills.get(skill_name)

        if not skill:
            logger.warning("Skill not found: %s", skill_name)
            return {"prompt_addition": "", "skill_name": skill_name, "found": False}

        logger.info(
            "Applied skill '%s' (%d chars of domain knowledge)",
            skill.name,
            len(skill.body),
        )

        return {
            "prompt_addition": (
                f"\n## ACTIVE SKILL: {skill.name}\n"
                f"{skill.description}\n\n"
                f"{skill.body}\n"
            ),
            "skill_name": skill.name,
            "found": True,
        }

    def get_skill_schemas(self) -> List[Dict[str, Any]]:
        """Return skill schemas for RuntimeState (backward compat)."""
        self.load_skills()
        return [
            {"name": s.name, "description": s.description}
            for s in self._skills.values()
        ]
