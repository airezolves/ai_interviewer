"""SQLAlchemy models — shared across services for schema consistency."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # null for OAuth users
    name = Column(String(255))
    auth_provider = Column(String(50), default="email")
    plan = Column(String(20), default="free")
    kits_generated_this_month = Column(Integer, default=0)
    monthly_reset_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    kits = relationship("Kit", back_populates="user", cascade="all, delete-orphan")


class Kit(Base):
    __tablename__ = "kits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255))
    role_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    jd_text = Column(Text, nullable=False)
    resume_text = Column(Text)
    resume_file_url = Column(String(500))
    structured_resume = Column(JSON)
    structured_jd = Column(JSON)
    match_analysis = Column(JSON)
    questions = Column(JSON)
    practical_test = Column(JSON)
    rubric = Column(JSON)
    red_flags = Column(JSON)
    flow_guide = Column(JSON)
    pdf_url = Column(String(500))
    share_token = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="kits")
    generation_job = relationship("GenerationJob", back_populates="kit", uselist=False)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kit_id = Column(UUID(as_uuid=True), ForeignKey("kits.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String(20), default="pending")
    current_step = Column(String(50))
    progress_pct = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    kit = relationship("Kit", back_populates="generation_job")


class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    raw_text = Column(Text)
    structured_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=func.now())
