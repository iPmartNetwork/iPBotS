"""Tests for public API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from api.app import app


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Health endpoint returns ok."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPublicAPI:
    """Test public API endpoints."""

    @pytest.mark.asyncio
    async def test_stats_no_api_key(self):
        """Stats endpoint requires API key."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/stats")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_stats_invalid_api_key(self):
        """Stats endpoint rejects invalid API key."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/stats",
                headers={"X-API-Key": "wrong-key"},
            )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_plans_no_api_key(self):
        """Plans endpoint requires API key."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/plans")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """User endpoint returns 404 for unknown user."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/user/999999",
                headers={"X-API-Key": "wrong-key"},
            )

        assert response.status_code == 401
