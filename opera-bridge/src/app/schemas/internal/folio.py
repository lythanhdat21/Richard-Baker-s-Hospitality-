from decimal import Decimal

from pydantic import BaseModel


class MoneyAmount(BaseModel):
    amount: Decimal | None = None
    currency_code: str | None = None


class FolioWindowSummary(BaseModel):
    window_no: int | None = None
    balance: MoneyAmount | None = None
    revenue: MoneyAmount | None = None
    payment: MoneyAmount | None = None
    folio_count: int = 0
    has_more: bool | None = None
    confidential: bool | None = None
    empty_window: bool | None = None


class FolioSummary(BaseModel):
    reservation_id: str
    windows: list[FolioWindowSummary]
    post_stay_charge_allowed: bool | None = None
    pre_stay_charge_allowed: bool | None = None
    room_and_tax_posted: bool | None = None


class PaymentStatus(BaseModel):
    reservation_id: str
    balance: MoneyAmount | None = None
    is_paid: bool | None = None
