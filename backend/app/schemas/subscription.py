"""Subscription document shape for users/{uid}/subscription/default."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

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


class CheckoutPlanBody(BaseModel):
    plan: SubscriptionPlan


class SubscriptionStatusResponse(BaseModel):
    status: SubscriptionStatus = "none"
    plan: SubscriptionPlan | None = None
    current_period_end: datetime | None = None
    trial_started_at: datetime | None = None
    trial_end: datetime | None = None
    source: SubscriptionSource | None = None
