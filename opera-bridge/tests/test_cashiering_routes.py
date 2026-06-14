import pytest
from httpx import ASGITransport, AsyncClient

from src.app.core.config import settings
from src.app.schemas.internal.folio import MoneyAmount, PaymentStatus
from src.main import app


@pytest.mark.asyncio
async def test_folio_requires_cashiering_role():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/reservations/RES001/folio",
            headers={"X-Internal-API-Key": settings.internal_api_key},
        )

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "CASHIERING_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_payment_status_allows_cashiering_role(monkeypatch):
    async def fake_get_payment_status(reservation_id: str, trace_id: str, actor_role: str):
        assert reservation_id == "RES001"
        assert trace_id
        assert actor_role == "cashiering"
        return PaymentStatus(
            reservation_id=reservation_id,
            balance=MoneyAmount(amount="0.00", currency_code="USD"),
            is_paid=True,
        )

    monkeypatch.setattr(
        "src.app.services.folio_service.get_payment_status",
        fake_get_payment_status,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/reservations/RES001/payment-status",
            headers={
                "X-Internal-API-Key": settings.internal_api_key,
                "X-Internal-Role": "cashiering",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["reservation_id"] == "RES001"
    assert body["data"]["is_paid"] is True
