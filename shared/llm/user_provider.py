"""Per-user LLM provider activation — loads the user's active provider from
the DB and pushes it into the ContextVar consumed by the model factory.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy import select

from shared.database import get_database
from shared.database.models import UserLLMProvider
from shared.llm import (
    ModelConfig,
    model_config_from_db_row,
    set_active_model,
    reset_active_model,
)


async def load_active_provider(user_id: str | uuid.UUID) -> Optional[ModelConfig]:
    """Return the user's active ModelConfig, or None if they have none configured."""
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(UserLLMProvider).where(
                UserLLMProvider.user_id == uid,
                UserLLMProvider.is_active.is_(True),
            )
        )
        row = result.scalar_one_or_none()
    if row is None:
        return None
    return model_config_from_db_row({
        "provider": row.provider,
        "model": row.model,
        "endpoint": row.endpoint,
        "api_key_encrypted": row.api_key_encrypted,
        "display_name": row.display_name,
    })


@asynccontextmanager
async def use_user_llm(user_id: str | uuid.UUID):
    """Context manager: bind the user's active provider for the enclosed scope.

    Falls back to env defaults if the user has no active provider.
    """
    cfg = await load_active_provider(user_id)
    token = set_active_model(cfg) if cfg else None
    try:
        yield cfg
    finally:
        if token is not None:
            reset_active_model(token)
