"""users/{uid}/subscription/default and stripe_customers/{customerId} index."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
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
SIGNUP_TRIAL_DAYS = 14


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


def ensure_signup_trial(
    db: Any,
    uid: str,
    now: datetime | None = None,
) -> UserSubscription:
    """
    Create an app-managed signup trial for new users if no subscription record exists.
    Idempotent: existing records are returned unchanged.
    """
    existing = get_subscription(db, uid)
    if existing is not None:
        return existing

    current = now or datetime.now(timezone.utc)
    trial_end = current + timedelta(days=SIGNUP_TRIAL_DAYS)
    rec = UserSubscription(
        stripe_customer_id=None,
        stripe_subscription_id=None,
        status="trialing",
        plan=None,
        current_period_end=None,
        trial_started_at=current,
        trial_end=trial_end,
        source="app_trial",
    )
    _upsert_subscription_doc(db, uid, rec)
    return rec


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


def _subscription_item_period_end(stripe_sub: dict[str, Any]) -> datetime | None:
    """Billing period end from subscription or first line item (newer Stripe API shapes)."""
    direct = _unix_ts_to_dt(stripe_sub.get("current_period_end"))
    if direct is not None:
        return direct
    items = stripe_sub.get("items") or {}
    data = items.get("data") if isinstance(items, dict) else None
    if not data or not isinstance(data[0], dict):
        return None
    return _unix_ts_to_dt(data[0].get("current_period_end"))


def _subscription_scheduled_end(
    stripe_sub: dict[str, Any],
) -> tuple[bool, datetime | None]:
    """Return Stripe cancel_at_period_end flag and when access ends, if scheduled."""
    cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end"))
    cancel_at = _unix_ts_to_dt(stripe_sub.get("cancel_at"))
    if cancel_at is not None:
        return cancel_at_period_end, cancel_at
    if cancel_at_period_end:
        return True, _subscription_item_period_end(stripe_sub)
    return False, None


_STRIPE_STATUS_PRIORITY: dict[str, int] = {
    "active": 0,
    "trialing": 1,
    "past_due": 2,
    "unpaid": 3,
    "canceled": 4,
    "incomplete_expired": 5,
    "incomplete": 6,
    "paused": 7,
}


def _stripe_sub_as_dict(sub: Any) -> dict[str, Any]:
    if isinstance(sub, dict):
        return sub
    if hasattr(sub, "to_dict"):
        d = sub.to_dict()
        return d if isinstance(d, dict) else dict(sub)
    return dict(sub)


def _pick_primary_stripe_subscription(subs: list[dict[str, Any]]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_prio = 999
    for raw in subs:
        sd = _stripe_sub_as_dict(raw)
        st = (sd.get("status") or "").strip()
        prio = _STRIPE_STATUS_PRIORITY.get(st, 50)
        if prio < best_prio:
            best_prio = prio
            best = sd
    return best


def reconcile_subscription_from_stripe(
    db: Any,
    uid: str,
    settings: Settings,
) -> UserSubscription | None:
    """
    Refresh Firestore from Stripe for users with a stored customer id.
    Handles resubscribe cases where an old subscription was deleted but a new active one exists.
    """
    import stripe

    existing = get_subscription(db, uid)
    customer_id = (existing.stripe_customer_id or "").strip() if existing else ""
    if not customer_id or not (settings.STRIPE_SECRET_KEY or "").strip():
        return existing

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        listed = stripe.Subscription.list(customer=customer_id, status="all", limit=20)
        stripe_subs = [_stripe_sub_as_dict(s) for s in listed.auto_paging_iter()]
    except stripe.StripeError as e:
        logger.warning("reconcile: list subscriptions failed customer=%s: %s", customer_id, e)
        return existing

    best = _pick_primary_stripe_subscription(stripe_subs)
    if not best:
        return existing

    best_id = (best.get("id") or "").strip()
    best_status_raw = (best.get("status") or "").strip()
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
    best_status = status_map.get(best_status_raw, "none")
    stored_id = (existing.stripe_subscription_id or "").strip() if existing else ""
    cancel_at_period_end, subscription_ends_at = _subscription_scheduled_end(best)
    current_period_end = _subscription_item_period_end(best)

    if (
        stored_id == best_id
        and existing
        and existing.status == best_status
        and existing.cancel_at_period_end == cancel_at_period_end
        and existing.subscription_ends_at == subscription_ends_at
        and existing.current_period_end == current_period_end
    ):
        return existing

    upsert_subscription_from_stripe_subscription(db, uid, customer_id, best, settings)
    return get_subscription(db, uid)


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
    current_period_end = _subscription_item_period_end(stripe_sub)
    trial_end = _unix_ts_to_dt(stripe_sub.get("trial_end"))
    cancel_at_period_end, subscription_ends_at = _subscription_scheduled_end(stripe_sub)

    rec = UserSubscription(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=sub_id if isinstance(sub_id, str) else None,
        status=status,
        plan=plan,
        current_period_end=current_period_end,
        trial_started_at=_unix_ts_to_dt(stripe_sub.get("trial_start")),
        trial_end=trial_end,
        source="stripe",
        cancel_at_period_end=cancel_at_period_end,
        subscription_ends_at=subscription_ends_at,
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
                trial_started_at=existing.trial_started_at,
                trial_end=existing.trial_end,
                source=existing.source,
                cancel_at_period_end=False,
                subscription_ends_at=None,
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
                trial_started_at=None,
                trial_end=None,
                source="stripe",
                cancel_at_period_end=False,
                subscription_ends_at=None,
            ),
        )


def apply_subscription_deleted(
    db: Any,
    uid: str,
    stripe_customer_id: str,
    settings: Settings | None = None,
) -> None:
    """customer.subscription.deleted — set canceled, then reconcile if user resubscribed."""
    mark_subscription_canceled(db, uid, stripe_customer_id)
    if settings is not None:
        reconcile_subscription_from_stripe(db, uid, settings)


def clear_stale_stripe_customer_link(
    db: Any,
    uid: str,
    stripe_customer_id: str,
) -> None:
    """
    Drop stored Stripe customer + subscription ids when that customer no longer exists in Stripe.
    Keeps trial/status/plan fields so the user can run Checkout without `customer` on retry.
    """
    stripe_customer_id = stripe_customer_id.strip()
    if not stripe_customer_id:
        return
    existing = get_subscription(db, uid)
    if not existing:
        return
    current = (existing.stripe_customer_id or "").strip()
    if current != stripe_customer_id:
        return
    cleared = existing.model_copy(
        update={
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
        }
    )
    _upsert_subscription_doc(db, uid, cleared)
    try:
        _stripe_customer_ref(db, stripe_customer_id).delete()
    except Exception as ex:
        logger.warning(
            "could not delete stripe_customers/%s: %s",
            stripe_customer_id,
            ex,
        )
