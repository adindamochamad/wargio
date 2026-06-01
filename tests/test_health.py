"""Test endpoint health — DoD Hari 1."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import aplikasi


@pytest.mark.asyncio
async def test_health_return_200() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://test") as klien:
        res = await klien.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "wargio-api"
