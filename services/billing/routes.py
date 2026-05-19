"""Billing service routes."""

from fastapi import APIRouter, Request, Header

from shared.schemas.common import APIResponse, HealthResponse
from services.billing.schemas import PlanInfo, CheckoutRequest, CheckoutResponse
from services.billing.service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(service="billing")


@router.get("/plans", response_model=APIResponse[list[PlanInfo]])
async def get_plans():
    """List available subscription plans."""
    service = BillingService()
    plans = service.get_plans()
    return APIResponse(data=plans)


@router.post("/checkout", response_model=APIResponse[CheckoutResponse])
async def create_checkout(
    request: CheckoutRequest,
    user_id: str = "anonymous",
    user_email: str = "user@example.com",
):
    """Create a Stripe checkout session."""
    service = BillingService()
    result = await service.create_checkout_session(
        user_id=user_id,
        email=user_email,
        plan=request.plan,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )
    return APIResponse(data=result)


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    service = BillingService()
    result = await service.handle_webhook(payload, stripe_signature or "")
    return result
