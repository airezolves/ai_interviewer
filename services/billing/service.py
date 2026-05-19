"""Billing service business logic."""

import stripe

from shared.utils.logger import get_logger
from shared.middleware.error_handler import ServiceException
from services.billing.config.settings import get_billing_settings
from services.billing.schemas import PlanInfo, CheckoutResponse

logger = get_logger(__name__)
settings = get_billing_settings()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = [
    PlanInfo(
        id="free",
        name="Free",
        price_monthly=0,
        price_annual=0,
        kits_per_month=3,
        features=[
            "3 interview kits/month",
            "Basic questions + rubric",
            "PDF export",
        ],
    ),
    PlanInfo(
        id="pro",
        name="Pro",
        price_monthly=39,
        price_annual=348,
        kits_per_month=100,
        features=[
            "100 interview kits/month",
            "Full kit (questions + assessment + rubric + red flags + flow guide)",
            "PDF export",
            "Shareable links",
            "Kit history & search",
            "Priority support",
        ],
    ),
    PlanInfo(
        id="team",
        name="Team",
        price_monthly=99,
        price_annual=948,
        kits_per_month=500,
        features=[
            "500 interview kits/month",
            "Everything in Pro",
            "Team workspaces",
            "Candidate comparison",
            "Debrief templates",
            "Team analytics",
        ],
    ),
]


class BillingService:
    """Handles Stripe billing operations."""

    def get_plans(self) -> list[PlanInfo]:
        return PLANS

    async def create_checkout_session(
        self, user_id: str, email: str, plan: str, success_url: str, cancel_url: str
    ) -> CheckoutResponse:
        """Create a Stripe Checkout session."""
        if not settings.STRIPE_SECRET_KEY:
            raise ServiceException("Stripe not configured", status_code=503)

        price_id = (
            settings.STRIPE_PRICE_PRO_MONTHLY
            if plan == "pro_monthly"
            else settings.STRIPE_PRICE_PRO_ANNUAL
        )

        if not price_id:
            raise ServiceException(f"Price not configured for plan: {plan}", status_code=400)

        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                customer_email=email,
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id},
            )
            return CheckoutResponse(checkout_url=session.url)

        except stripe.error.StripeError as e:
            logger.error("stripe_checkout_error", error=str(e))
            raise ServiceException(f"Stripe error: {e.user_message}", status_code=400)

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Handle Stripe webhook events."""
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ServiceException("Webhook secret not configured", status_code=503)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise ServiceException("Invalid webhook signature", status_code=400)

        # Handle relevant events
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"].get("user_id")
            logger.info("checkout_completed", user_id=user_id)
            # TODO: Update user plan in auth service

        elif event["type"] == "customer.subscription.deleted":
            logger.info("subscription_cancelled")
            # TODO: Downgrade user to free plan

        return {"status": "handled", "type": event["type"]}
