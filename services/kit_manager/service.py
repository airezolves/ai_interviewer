"""Kit Manager service — orchestrates kit generation."""

import secrets
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.utils.logger import get_logger
from shared.middleware.error_handler import NotFoundException, ServiceException
from services.kit_manager.models import Kit, KitSection, Feedback
from services.kit_manager.schemas import (
    CreateKitRequest,
    KitSummary,
    KitDetail,
    FeedbackRequest,
)
from services.kit_manager.config.settings import get_kit_manager_settings

logger = get_logger(__name__)
settings = get_kit_manager_settings()


class KitManagerService:
    """Manages kit lifecycle and storage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_kit(self, user_id: UUID, request: CreateKitRequest) -> Kit:
        """Create a new kit record (status=pending)."""
        title = request.title or f"Interview Kit - {request.role_type.replace('_', ' ').title()}"

        kit = Kit(
            user_id=user_id,
            title=title,
            role_type=request.role_type,
            jd_text=request.jd_text,
            candidate_name=request.candidate_name,
            status="pending",
        )
        self.db.add(kit)
        await self.db.flush()
        await self.db.refresh(kit)

        logger.info("kit_created", kit_id=str(kit.id), user_id=str(user_id))
        return kit

    async def store_kit_result(self, kit_id: UUID, generated_kit: dict):
        """Store the AI-generated kit sections."""
        result = await self.db.execute(select(Kit).where(Kit.id == kit_id))
        kit = result.scalar_one_or_none()

        if not kit:
            raise NotFoundException("Kit", str(kit_id))

        # Store each section
        section_types = ["jd_analysis", "questions", "assessment", "rubric", "red_flags", "flow_guide"]

        for section_type in section_types:
            content = generated_kit.get(section_type, {})
            if content:
                section = KitSection(
                    kit_id=kit_id,
                    section_type=section_type,
                    content=content,
                )
                self.db.add(section)

        kit.status = "completed"
        await self.db.flush()
        logger.info("kit_result_stored", kit_id=str(kit_id))

    async def mark_kit_failed(self, kit_id: UUID, error: str):
        """Mark a kit as failed."""
        result = await self.db.execute(select(Kit).where(Kit.id == kit_id))
        kit = result.scalar_one_or_none()
        if kit:
            kit.status = "failed"
            await self.db.flush()
            logger.error("kit_generation_failed", kit_id=str(kit_id), error=error)

    async def get_kit(self, kit_id: UUID, user_id: UUID | None = None) -> KitDetail:
        """Get a full kit with all sections."""
        query = select(Kit).options(selectinload(Kit.sections)).where(Kit.id == kit_id)
        if user_id:
            query = query.where(Kit.user_id == user_id)

        result = await self.db.execute(query)
        kit = result.scalar_one_or_none()

        if not kit:
            raise NotFoundException("Kit", str(kit_id))

        # Build sections dict
        sections = {}
        for section in kit.sections:
            sections[section.section_type] = section.content

        return KitDetail(
            id=kit.id,
            title=kit.title,
            role_type=kit.role_type,
            candidate_name=kit.candidate_name,
            status=kit.status,
            jd_text=kit.jd_text,
            sections=sections,
            share_token=kit.share_token,
            created_at=kit.created_at,
            updated_at=kit.updated_at,
        )

    async def list_kits(self, user_id: UUID, page: int = 1, page_size: int = 20) -> list[KitSummary]:
        """List user's kits (paginated)."""
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Kit)
            .where(Kit.user_id == user_id)
            .order_by(Kit.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        kits = result.scalars().all()
        return [KitSummary.model_validate(k) for k in kits]

    async def delete_kit(self, kit_id: UUID, user_id: UUID):
        """Delete a kit."""
        result = await self.db.execute(
            select(Kit).where(Kit.id == kit_id, Kit.user_id == user_id)
        )
        kit = result.scalar_one_or_none()
        if not kit:
            raise NotFoundException("Kit", str(kit_id))

        await self.db.delete(kit)
        await self.db.flush()

    async def generate_share_link(self, kit_id: UUID, user_id: UUID) -> str:
        """Generate a shareable token for a kit."""
        result = await self.db.execute(
            select(Kit).where(Kit.id == kit_id, Kit.user_id == user_id)
        )
        kit = result.scalar_one_or_none()
        if not kit:
            raise NotFoundException("Kit", str(kit_id))

        if not kit.share_token:
            kit.share_token = secrets.token_urlsafe(32)
            await self.db.flush()

        return kit.share_token

    async def get_shared_kit(self, token: str) -> KitDetail:
        """Get a kit by its share token (public access)."""
        query = select(Kit).options(selectinload(Kit.sections)).where(Kit.share_token == token)
        result = await self.db.execute(query)
        kit = result.scalar_one_or_none()

        if not kit:
            raise NotFoundException("Shared kit", token)

        sections = {}
        for section in kit.sections:
            sections[section.section_type] = section.content

        return KitDetail(
            id=kit.id,
            title=kit.title,
            role_type=kit.role_type,
            candidate_name=kit.candidate_name,
            status=kit.status,
            jd_text=kit.jd_text,
            sections=sections,
            share_token=kit.share_token,
            created_at=kit.created_at,
            updated_at=kit.updated_at,
        )

    async def submit_feedback(self, kit_id: UUID, user_id: UUID, request: FeedbackRequest):
        """Submit feedback on a kit."""
        feedback = Feedback(
            kit_id=kit_id,
            user_id=user_id,
            rating=request.rating,
            questions_useful=request.questions_useful,
            assessment_appropriate=request.assessment_appropriate,
            comments=request.comments,
        )
        self.db.add(feedback)
        await self.db.flush()
