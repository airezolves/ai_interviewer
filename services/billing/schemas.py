"""Billing service schemas."""

from uuid import UUID
from pydantic import BaseModel


class PlanInfo(BaseModel):
    id: str
    name: str
    price_monthly: int
    price_annual: int
    kits_per_month: int
    features: list[str]


class SubscriptionInfo(BaseModel):
    user_id: UUID
    plan: str
    status: str  # active, cancelled, past_due
    current_period_end: str | None = None
    cancel_at_period_end: bool = False


class CheckoutRequest(BaseModel):
    plan: str  # "pro_monthly" or "pro_annual"
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class UsageInfo(BaseModel):
    kits_generated: int
    kits_limit: int
    period_start: str
    period_end: str
