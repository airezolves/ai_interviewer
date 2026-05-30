"""LLM provider CRUD — per-user encrypted API keys for the LangGraph flow."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select, update

from shared.config import BaseAppSettings
from shared.database import get_database
from shared.database.models import UserLLMProvider
from shared.schemas.llm_provider import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderRead,
)
from shared.security import encrypt_secret, decrypt_secret, mask_secret

router = APIRouter()


def _master_key() -> str:
    key = BaseAppSettings().ai_encryption_master_key or ""
    if not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI_ENCRYPTION_MASTER_KEY not configured on server",
        )
    return key


def _to_read(row: UserLLMProvider) -> LLMProviderRead:
    masked = ""
    if row.api_key_encrypted:
        try:
            plain = decrypt_secret(row.api_key_encrypted, _master_key())
            masked = mask_secret(plain)
        except Exception:
            masked = "••••••(error)"
    return LLMProviderRead(
        id=row.id,
        provider=row.provider,
        model=row.model,
        display_name=row.display_name,
        endpoint=row.endpoint,
        api_key_masked=masked,
        is_active=row.is_active,
        created_at=row.created_at,
    )


@router.get("/users/{user_id}/llm-providers", response_model=list[LLMProviderRead])
async def list_providers(user_id: str):
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(UserLLMProvider)
            .where(UserLLMProvider.user_id == uuid.UUID(user_id))
            .order_by(UserLLMProvider.created_at.desc())
        )
        rows = result.scalars().all()
    return [_to_read(r) for r in rows]


@router.post("/users/{user_id}/llm-providers", response_model=LLMProviderRead, status_code=201)
async def create_provider(user_id: str, payload: LLMProviderCreate):
    if payload.provider == "openai-compatible" and not payload.endpoint:
        raise HTTPException(400, "`endpoint` is required for openai-compatible provider")

    encrypted = encrypt_secret(payload.api_key, _master_key())
    db = get_database()
    async with db.async_session() as session:
        if payload.is_active:
            await session.execute(
                update(UserLLMProvider)
                .where(UserLLMProvider.user_id == uuid.UUID(user_id))
                .values(is_active=False)
            )
        row = UserLLMProvider(
            user_id=uuid.UUID(user_id),
            provider=payload.provider,
            model=payload.model,
            display_name=payload.display_name or payload.model,
            endpoint=payload.endpoint,
            api_key_encrypted=encrypted,
            is_active=payload.is_active,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return _to_read(row)


@router.patch("/users/{user_id}/llm-providers/{provider_id}", response_model=LLMProviderRead)
async def update_provider(user_id: str, provider_id: str, payload: LLMProviderUpdate):
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(UserLLMProvider).where(
                UserLLMProvider.id == uuid.UUID(provider_id),
                UserLLMProvider.user_id == uuid.UUID(user_id),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Provider not found")

        if payload.is_active is True:
            await session.execute(
                update(UserLLMProvider)
                .where(
                    UserLLMProvider.user_id == uuid.UUID(user_id),
                    UserLLMProvider.id != uuid.UUID(provider_id),
                )
                .values(is_active=False)
            )

        if payload.model is not None:
            row.model = payload.model
        if payload.display_name is not None:
            row.display_name = payload.display_name
        if payload.endpoint is not None:
            row.endpoint = payload.endpoint
        if payload.api_key is not None:
            row.api_key_encrypted = encrypt_secret(payload.api_key, _master_key())
        if payload.is_active is not None:
            row.is_active = payload.is_active
        await session.commit()
        await session.refresh(row)
    return _to_read(row)


@router.post("/users/{user_id}/llm-providers/{provider_id}/activate", response_model=LLMProviderRead)
async def activate_provider(user_id: str, provider_id: str):
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(UserLLMProvider).where(
                UserLLMProvider.id == uuid.UUID(provider_id),
                UserLLMProvider.user_id == uuid.UUID(user_id),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Provider not found")

        await session.execute(
            update(UserLLMProvider)
            .where(UserLLMProvider.user_id == uuid.UUID(user_id))
            .values(is_active=False)
        )
        row.is_active = True
        await session.commit()
        await session.refresh(row)
    return _to_read(row)


@router.delete("/users/{user_id}/llm-providers/{provider_id}", status_code=204)
async def delete_provider(user_id: str, provider_id: str):
    db = get_database()
    async with db.async_session() as session:
        result = await session.execute(
            select(UserLLMProvider).where(
                UserLLMProvider.id == uuid.UUID(provider_id),
                UserLLMProvider.user_id == uuid.UUID(user_id),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(404, "Provider not found")
        await session.delete(row)
        await session.commit()
    return None
