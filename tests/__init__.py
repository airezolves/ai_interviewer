"""Test configuration and shared fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture
async def gateway_client():
    """Async test client for gateway."""
    from services.gateway.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_client():
    """Async test client for auth service."""
    from services.auth.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def ai_engine_client():
    """Async test client for AI engine service."""
    from services.ai_engine.app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
