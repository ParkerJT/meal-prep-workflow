"""Subscription document shape for users/{uid}/subscription/default."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SubscriptionStatus = Literal["active", "trialing", "past_due", "canceled", "none"]
SubscriptionPlan = Literal["monthly", "annual"]
SubscriptionSource = Literal["app_trial", "stripe"]


class UserSubscription(BaseModel):
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    status: SubscriptionStatus
    plan: SubscriptionPlan | None = None
    current_period_end: datetime | None = None
    trial_started_at: datetime | None = None
    trial_end: datetime | None = None
    source: SubscriptionSource | None = None
    cancel_at_period_end: bool = False
    subscription_ends_at: datetime | None = None


class CheckoutPlanBody(BaseModel):
    plan: SubscriptionPlan


class SubscriptionStatusResponse(BaseModel):
    status: SubscriptionStatus = "none"
    plan: SubscriptionPlan | None = None
    current_period_end: datetime | None = None
    trial_started_at: datetime | None = None
    trial_end: datetime | None = None
    source: SubscriptionSource | None = None
    cancel_at_period_end: bool = False
    subscription_ends_at: datetime | None = None
    billing_portal_available: bool = Field(
        default=False,
        description="True when this user has a Stripe Customer (portal / invoices available).",
    )


def subscription_status_response(sub: UserSubscription) -> SubscriptionStatusResponse:
    return SubscriptionStatusResponse(
        status=sub.status,
        plan=sub.plan,
        current_period_end=sub.current_period_end,
        trial_started_at=sub.trial_started_at,
        trial_end=sub.trial_end,
        source=sub.source,
        cancel_at_period_end=sub.cancel_at_period_end,
        subscription_ends_at=sub.subscription_ends_at,
        billing_portal_available=bool(sub.stripe_customer_id),
    )
