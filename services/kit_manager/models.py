"""Kit Manager database models."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Enum as SAEnum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database.base_model import Base, TimestampMixin, UUIDMixin


class Kit(Base, UUIDMixin, TimestampMixin):
    """Interview kit model."""

    __tablename__ = "kits"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    role_type: Mapped[str] = mapped_column(String(100), nullable=False)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    candidate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, generating, completed, failed
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    # Relationships
    sections: Mapped[list["KitSection"]] = relationship(back_populates="kit", cascade="all, delete-orphan")


class KitSection(Base, UUIDMixin, TimestampMixin):
    """Individual section of an interview kit."""

    __tablename__ = "kit_sections"

    kit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kits.id", ondelete="CASCADE"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # jd_analysis, questions, assessment, rubric, red_flags, flow_guide
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    kit: Mapped["Kit"] = relationship(back_populates="sections")


class Feedback(Base, UUIDMixin, TimestampMixin):
    """User feedback on a kit."""

    __tablename__ = "feedback"

    kit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kits.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    questions_useful: Mapped[bool | None] = mapped_column(nullable=True)
    assessment_appropriate: Mapped[bool | None] = mapped_column(nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
