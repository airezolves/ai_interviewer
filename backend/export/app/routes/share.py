"""Shareable link routes."""

import uuid
from fastapi import APIRouter, HTTPException, Header
from sqlalchemy import select

from shared.database import get_database
from shared.database.models import Kit

router = APIRouter()


@router.post("/share/{kit_id}")
async def create_share_link(kit_id: str, x_user_id: str = Header(...)):
    """Generate a shareable link for a kit."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(Kit).where(Kit.id == uuid.UUID(kit_id), Kit.user_id == uuid.UUID(x_user_id))
        )
        kit = result.scalar_one_or_none()

    if not kit:
        raise HTTPException(status_code=404, detail="Kit not found")

    return {
        "share_url": f"/api/v1/export/shared/{kit.share_token}",
        "share_token": str(kit.share_token),
    }
