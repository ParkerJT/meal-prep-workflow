"""Subscription document shape for users/{uid}/subscription/default."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SubscriptionStatus = Literal["active", "trialing", "past_due", "canceled", "none"]
SubscriptionPlan = Literal["monthly", "annual"]


class UserSubscription(BaseModel):
    stripe_customer_id: str
    stripe_subscription_id: str | None = None
    status: SubscriptionStatus
    plan: SubscriptionPlan | None = None
    current_period_end: datetime | None = None
    trial_end: datetime | None = None


class CheckoutPlanBody(BaseModel):
    plan: SubscriptionPlan
