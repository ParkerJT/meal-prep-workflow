"""Stripe Checkout and Customer Portal session creation."""

from __future__ import annotations

from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings
from app.dependencies import get_current_uid, get_firestore
from app.schemas.subscription import CheckoutPlanBody, SubscriptionStatusResponse
from app.services.firestore.subscription import ensure_signup_trial, get_subscription

router = APIRouter(prefix="/api/subscription", tags=["subscription"])
settings = Settings()


def _require_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe secret key not configured",
        )


def _require_checkout_urls() -> None:
    if not (settings.STRIPE_CHECKOUT_SUCCESS_URL or "").strip() or not (
        settings.STRIPE_CHECKOUT_CANCEL_URL or ""
    ).strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="STRIPE_CHECKOUT_SUCCESS_URL and STRIPE_CHECKOUT_CANCEL_URL must be set",
        )


def _require_portal_return_url() -> None:
    if not (settings.STRIPE_BILLING_PORTAL_RETURN_URL or "").strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="STRIPE_BILLING_PORTAL_RETURN_URL must be set",
        )


@router.post("/checkout")
def create_checkout_session(
    body: CheckoutPlanBody,
    uid: str = Depends(get_current_uid),
) -> dict[str, str]:
    """Create a Stripe Checkout Session for selected paid plan. Returns checkout URL."""
    _require_stripe()
    _require_checkout_urls()

    price_id = (
        settings.STRIPE_PRICE_MONTHLY
        if body.plan == "monthly"
        else settings.STRIPE_PRICE_ANNUAL
    )
    price_id = (price_id or "").strip()
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STRIPE_PRICE_{body.plan.upper()} not configured",
        )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=settings.STRIPE_CHECKOUT_SUCCESS_URL.strip(),
            cancel_url=settings.STRIPE_CHECKOUT_CANCEL_URL.strip(),
            client_reference_id=uid,
            metadata={"firebase_uid": uid},
            subscription_data={"metadata": {"firebase_uid": uid}},
        )
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {getattr(e, 'user_message', None) or str(e)}",
        ) from e

    url = session.get("url") if isinstance(session, dict) else getattr(session, "url", None)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a checkout URL",
        )
    return {"url": url}


@router.post("/start-trial", response_model=SubscriptionStatusResponse)
def start_signup_trial(
    uid: str = Depends(get_current_uid),
    db: Any = Depends(get_firestore),
) -> SubscriptionStatusResponse:
    """
    Start 14-day no-card trial for new users only.
    Idempotent: returns existing subscription document unchanged when present.
    """
    sub = ensure_signup_trial(db, uid)
    return SubscriptionStatusResponse(
        status=sub.status,
        plan=sub.plan,
        current_period_end=sub.current_period_end,
        trial_started_at=sub.trial_started_at,
        trial_end=sub.trial_end,
        source=sub.source,
    )


@router.get("/me", response_model=SubscriptionStatusResponse)
def get_my_subscription_status(
    uid: str = Depends(get_current_uid),
    db: Any = Depends(get_firestore),
) -> SubscriptionStatusResponse:
    sub = get_subscription(db, uid)
    if not sub:
        return SubscriptionStatusResponse(status="none")
    return SubscriptionStatusResponse(
        status=sub.status,
        plan=sub.plan,
        current_period_end=sub.current_period_end,
        trial_started_at=sub.trial_started_at,
        trial_end=sub.trial_end,
        source=sub.source,
    )


@router.post("/portal")
def create_billing_portal_session(
    uid: str = Depends(get_current_uid),
    db: Any = Depends(get_firestore),
) -> dict[str, str]:
    """Create a Stripe Customer Portal session for subscription management."""
    _require_stripe()
    _require_portal_return_url()

    sub = get_subscription(db, uid)
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No billing profile found yet. Choose a paid plan first.",
        )

    try:
        session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=settings.STRIPE_BILLING_PORTAL_RETURN_URL.strip(),
        )
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {getattr(e, 'user_message', None) or str(e)}",
        ) from e

    url = session.get("url") if isinstance(session, dict) else getattr(session, "url", None)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a portal URL",
        )
    return {"url": url}
