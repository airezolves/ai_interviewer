"""Kit Manager service schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateKitRequest(BaseModel):
    """Request to create a new interview kit."""
    jd_text: str = Field(min_length=50, max_length=10000)
    resume_data: dict
    role_type: str = "data_scientist"
    candidate_name: str | None = None
    title: str | None = None


class KitSummary(BaseModel):
    """Brief kit listing."""
    id: UUID
    title: str
    role_type: str
    candidate_name: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KitDetail(BaseModel):
    """Full kit with all sections."""
    id: UUID
    title: str
    role_type: str
    candidate_name: str | None
    status: str
    jd_text: str
    sections: dict  # {section_type: content}
    share_token: str | None
    created_at: datetime
    updated_at: datetime


class KitStatusResponse(BaseModel):
    """Kit generation status."""
    kit_id: UUID
    status: str  # pending, generating, completed, failed
    progress: int = 0  # 0-100
    message: str | None = None


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    questions_useful: bool | None = None
    assessment_appropriate: bool | None = None
    comments: str | None = None


class ShareLinkResponse(BaseModel):
    share_url: str
    expires_in_days: int = 30
