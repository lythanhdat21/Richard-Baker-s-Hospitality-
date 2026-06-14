from decimal import Decimal, InvalidOperation
from typing import Any

from src.app.schemas.internal.folio import FolioSummary, FolioWindowSummary, MoneyAmount, PaymentStatus


def _money(value: dict[str, Any] | None) -> MoneyAmount | None:
    if not isinstance(value, dict):
        return None

    raw_amount = value.get("amount")
    amount = None
    if raw_amount is not None:
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError):
            amount = None

    currency_code = value.get("currencyCode") or value.get("currency_code")
    if amount is None and currency_code is None:
        return None

    return MoneyAmount(amount=amount, currency_code=currency_code)


def to_internal_folio_summary(opera_folio: dict[str, Any], reservation_id: str) -> FolioSummary:
    info = opera_folio.get("reservationFolioInformation") or {}
    windows = info.get("folioWindows") or []

    return FolioSummary(
        reservation_id=reservation_id,
        windows=[
            FolioWindowSummary(
                window_no=window.get("folioWindowNo"),
                balance=_money(window.get("balance")),
                revenue=_money(window.get("revenue")),
                payment=_money(window.get("payment")),
                folio_count=len(window.get("folios") or []),
                has_more=window.get("hasMore"),
                confidential=window.get("confidential"),
                empty_window=window.get("emptyWindow"),
            )
            for window in windows
            if isinstance(window, dict)
        ],
        post_stay_charge_allowed=info.get("postStayChargeAllowed"),
        pre_stay_charge_allowed=info.get("preStayChargeAllowed"),
        room_and_tax_posted=info.get("roomAndTaxPosted"),
    )


def to_internal_payment_status(opera_balance: dict[str, Any], reservation_id: str) -> PaymentStatus:
    balance = _money(opera_balance.get("paymentBalance"))
    is_paid = None
    if balance and balance.amount is not None:
        is_paid = balance.amount <= Decimal("0")

    return PaymentStatus(reservation_id=reservation_id, balance=balance, is_paid=is_paid)
