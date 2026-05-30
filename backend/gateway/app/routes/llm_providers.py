"""LLM provider routes — gateway proxy to auth service for the current user."""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from backend.gateway.app.config import get_settings
from backend.gateway.app.middleware.auth import get_current_user
from shared.auth import TokenData
from shared.schemas.llm_provider import LLMProviderCreate, LLMProviderUpdate

router = APIRouter()


@router.get("")
async def list_my_providers(user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.auth_service_url}/users/{user.user_id}/llm-providers",
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.post("", status_code=201)
async def create_my_provider(payload: LLMProviderCreate, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/users/{user.user_id}/llm-providers",
            json=payload.model_dump(),
            timeout=10.0,
        )
    if resp.status_code != 201:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.patch("/{provider_id}")
async def update_my_provider(provider_id: str, payload: LLMProviderUpdate, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{settings.auth_service_url}/users/{user.user_id}/llm-providers/{provider_id}",
            json=payload.model_dump(exclude_unset=True),
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.post("/{provider_id}/activate")
async def activate_my_provider(provider_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.auth_service_url}/users/{user.user_id}/llm-providers/{provider_id}/activate",
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()


@router.delete("/{provider_id}", status_code=204)
async def delete_my_provider(provider_id: str, user: TokenData = Depends(get_current_user)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{settings.auth_service_url}/users/{user.user_id}/llm-providers/{provider_id}",
            timeout=10.0,
        )
    if resp.status_code not in (200, 204):
        raise HTTPException(resp.status_code, resp.text)
    return None
