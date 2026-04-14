"""users/{uid}/subscription/default and stripe_customers/{customerId} index."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from app.config import Settings
from app.schemas.subscription import SubscriptionPlan, SubscriptionStatus, UserSubscription
from app.services.firestore.timestamps import deep_convert_firestore_data, dump_datetimes_for_firestore

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

SUBSCRIPTION_SUBCOLLECTION = "subscription"
SUBSCRIPTION_DOC_ID = "default"
STRIPE_CUSTOMERS_COLLECTION = "stripe_customers"


def _subscription_ref(db: Any, uid: str):
    return (
        db.collection("users")
        .document(uid)
        .collection(SUBSCRIPTION_SUBCOLLECTION)
        .document(SUBSCRIPTION_DOC_ID)
    )


def _stripe_customer_ref(db: Any, stripe_customer_id: str):
    return db.collection(STRIPE_CUSTOMERS_COLLECTION).document(stripe_customer_id)


def set_customer_uid_mapping(db: Any, stripe_customer_id: str, uid: str) -> None:
    _stripe_customer_ref(db, stripe_customer_id).set({"uid": uid})


def get_uid_for_customer(db: Any, stripe_customer_id: str) -> str | None:
    snap = _stripe_customer_ref(db, stripe_customer_id).get()
    if not snap.exists:
        return None
    data = snap.to_dict() or {}
    return data.get("uid")


def get_subscription(db: Any, uid: str) -> UserSubscription | None:
    snap = _subscription_ref(db, uid).get()
    if not snap.exists:
        return None
    data = deep_convert_firestore_data(snap.to_dict() or {})
    return UserSubscription.model_validate(data)


def _upsert_subscription_doc(db: Any, uid: str, sub: UserSubscription) -> None:
    payload = dump_datetimes_for_firestore(sub.model_dump(mode="python"))
    _subscription_ref(db, uid).set(payload)


def price_id_to_plan(price_id: str, settings: Settings) -> SubscriptionPlan | None:
    monthly = (settings.STRIPE_PRICE_MONTHLY or "").strip()
    annual = (settings.STRIPE_PRICE_ANNUAL or "").strip()
    if price_id == monthly:
        return "monthly"
    if price_id == annual:
        return "annual"
    return None


def _stripe_subscription_to_plan(
    stripe_sub: dict[str, Any],
    settings: Settings,
) -> SubscriptionPlan | None:
    items = stripe_sub.get("items") or {}
    data = items.get("data") if isinstance(items, dict) else None
    if not data:
        return None
    first = data[0] if data else None
    if not first or not isinstance(first, dict):
        return None
    price = first.get("price") or {}
    if not isinstance(price, dict):
        return None
    pid = price.get("id")
    if not pid:
        return None
    return price_id_to_plan(pid, settings)


def _unix_ts_to_dt(ts: Any) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def upsert_subscription_from_stripe_subscription(
    db: Any,
    uid: str,
    stripe_customer_id: str,
    stripe_sub: dict[str, Any],
    settings: Settings,
) -> None:
    """Persist fields from Stripe Subscription object (dict)."""
    sub_id = stripe_sub.get("id")
    status_raw = (stripe_sub.get("status") or "").strip()
    status_map: dict[str, SubscriptionStatus] = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "canceled": "canceled",
        "unpaid": "past_due",
        "incomplete": "none",
        "incomplete_expired": "canceled",
        "paused": "none",
    }
    status: SubscriptionStatus = status_map.get(status_raw, "none")
    if status_raw not in status_map:
        logger.warning("unknown stripe subscription status: %s", status_raw)

    plan = _stripe_subscription_to_plan(stripe_sub, settings)
    current_period_end = _unix_ts_to_dt(stripe_sub.get("current_period_end"))
    trial_end = _unix_ts_to_dt(stripe_sub.get("trial_end"))

    rec = UserSubscription(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=sub_id if isinstance(sub_id, str) else None,
        status=status,
        plan=plan,
        current_period_end=current_period_end,
        trial_end=trial_end,
    )
    _upsert_subscription_doc(db, uid, rec)


def mark_subscription_canceled(db: Any, uid: str, stripe_customer_id: str) -> None:
    existing = get_subscription(db, uid)
    if existing:
        _upsert_subscription_doc(
            db,
            uid,
            UserSubscription(
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=existing.stripe_subscription_id,
                status="canceled",
                plan=existing.plan,
                current_period_end=existing.current_period_end,
                trial_end=existing.trial_end,
            ),
        )
    else:
        _upsert_subscription_doc(
            db,
            uid,
            UserSubscription(
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=None,
                status="canceled",
                plan=None,
                current_period_end=None,
                trial_end=None,
            ),
        )


def apply_subscription_deleted(db: Any, uid: str, stripe_customer_id: str) -> None:
    """customer.subscription.deleted — set canceled per BUILD_PLAN."""
    mark_subscription_canceled(db, uid, stripe_customer_id)
