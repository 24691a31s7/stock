"""
Integration tests that hit real network data via yfinance and the live
FastAPI app. These are slower and require internet access — mark them
so they can be skipped in restricted CI sandboxes with:
    pytest -m "not integration"
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_endpoint_end_to_end():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        resp = await client.get("/api/v1/analyze/AAPL")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ticker"] == "AAPL"
        assert body["recommendation"]["decision"] in {"BUY", "SELL", "HOLD", "WATCHLIST"}
        assert 0 <= body["prediction"]["profit_probability"] <= 100
        assert body["risk"]["risk_label"] in {"Low", "Medium", "High"}


@pytest.mark.asyncio
async def test_analyze_endpoint_invalid_ticker_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analyze/" + "X" * 20)
        assert resp.status_code == 400
