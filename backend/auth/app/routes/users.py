"""User routes — profile, usage tracking."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from shared.database import get_database
from shared.database.models import User
from shared.schemas.auth import UserResponse

router = APIRouter()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID (internal service call)."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users/{user_id}/increment-usage")
async def increment_usage(user_id: str):
    """Increment kit generation count (called by Kit Orchestrator)."""
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.kits_generated_this_month += 1
        await session.commit()

    return {"success": True, "kits_this_month": user.kits_generated_this_month}


@router.get("/users/{user_id}/can-generate")
async def can_generate(user_id: str):
    """Check if user can generate another kit (usage limits)."""
    from backend.auth.app.config import get_settings
    settings = get_settings()

    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.plan == "pro":
        return {"allowed": True, "reason": "Pro plan — unlimited"}

    allowed = user.kits_generated_this_month < settings.rate_limit_free_kits_per_month
    return {
        "allowed": allowed,
        "reason": f"{user.kits_generated_this_month}/{settings.rate_limit_free_kits_per_month} free kits used"
        if not allowed else "Within free tier limits",
        "kits_used": user.kits_generated_this_month,
        "kits_limit": settings.rate_limit_free_kits_per_month,
    }
