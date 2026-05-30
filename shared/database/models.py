"""SQLAlchemy models — shared across services for schema consistency."""

import uuid
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Numeric, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


# ─────────────────────────────────────────────────────────────────────
#  Users
# ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255))
    auth_provider = Column(String(50), default="email")
    plan = Column(String(20), default="free")
    kits_generated_this_month = Column(Integer, default=0)
    monthly_reset_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    kits = relationship("Kit", back_populates="user", cascade="all, delete-orphan")
    llm_providers = relationship("UserLLMProvider", back_populates="user", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────
#  Kits
# ─────────────────────────────────────────────────────────────────────
class Kit(Base):
    __tablename__ = "kits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255))
    role_type = Column(String(50), nullable=False)
    # State machine: pending → matching → match_ready → (denied | interviewing) → analyzed → complete | failed
    status = Column(String(20), default="pending")
    jd_text = Column(Text, nullable=False)
    resume_text = Column(Text)
    resume_file_url = Column(String(500))
    structured_resume = Column(JSONB)
    structured_jd = Column(JSONB)
    match_analysis = Column(JSONB)
    proceed_decision = Column(String(20))
    proceed_decided_at = Column(DateTime(timezone=True))
    pdf_url = Column(String(500))
    share_token = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="kits")
    generation_job = relationship("GenerationJob", back_populates="kit", uselist=False, cascade="all, delete-orphan")
    interview_session = relationship("InterviewSession", back_populates="kit", uselist=False, cascade="all, delete-orphan")
    final_analysis = relationship("FinalAnalysis", back_populates="kit", uselist=False, cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────
#  Generation jobs
# ─────────────────────────────────────────────────────────────────────
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

    kit = relationship("Kit", back_populates="generation_job")


# ─────────────────────────────────────────────────────────────────────
#  Parsed resumes cache
# ─────────────────────────────────────────────────────────────────────
class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    raw_text = Column(Text)
    structured_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=func.now())


# ─────────────────────────────────────────────────────────────────────
#  Per-user LLM providers (encrypted keys)
# ─────────────────────────────────────────────────────────────────────
class UserLLMProvider(Base):
    __tablename__ = "user_llm_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(150), nullable=False)
    display_name = Column(String(200))
    endpoint = Column(String(500))
    api_key_encrypted = Column(Text)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="llm_providers")


# ─────────────────────────────────────────────────────────────────────
#  Interview sessions
# ─────────────────────────────────────────────────────────────────────
class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kit_id = Column(UUID(as_uuid=True), ForeignKey("kits.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="in_progress")
    plan = Column(JSONB)
    current_turn_index = Column(Integer, nullable=False, default=0)
    max_turns = Column(Integer, nullable=False, default=10)
    started_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True))

    kit = relationship("Kit", back_populates="interview_session")
    turns = relationship("QATurn", back_populates="session", cascade="all, delete-orphan", order_by="QATurn.turn_index")


# ─────────────────────────────────────────────────────────────────────
#  Q&A turns
# ─────────────────────────────────────────────────────────────────────
class QATurn(Base):
    __tablename__ = "qa_turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_index", name="uq_qa_turns_session_id_turn_index"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_index = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    question_type = Column(String(30))
    topic = Column(String(150))
    agent_thoughts = Column(Text)
    answer = Column(Text)
    asked_at = Column(DateTime(timezone=True), default=func.now())
    answered_at = Column(DateTime(timezone=True))

    session = relationship("InterviewSession", back_populates="turns")


# ─────────────────────────────────────────────────────────────────────
#  Final analyses
# ─────────────────────────────────────────────────────────────────────
class FinalAnalysis(Base):
    __tablename__ = "final_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kit_id = Column(UUID(as_uuid=True), ForeignKey("kits.id", ondelete="CASCADE"), nullable=False, unique=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Numeric(5, 2))
    dimension_scores = Column(JSONB)
    pros = Column(JSONB)
    cons = Column(JSONB)
    recommendation = Column(String(20))                   # hire | no_hire | maybe
    role_suitability = Column(Text)
    reasoning = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    kit = relationship("Kit", back_populates="final_analysis")
