"""
Dispatch Stripe webhook events and persist subscription state to Firestore.
"""

from __future__ import annotations

import logging
from typing import Any

import stripe

from app.config import Settings
from app.services.firestore.subscription import (
    apply_subscription_deleted,
    get_uid_for_customer,
    set_customer_uid_mapping,
    upsert_subscription_from_stripe_subscription,
)

logger = logging.getLogger(__name__)


def handle_stripe_event(event: Any, db: Any, settings: Settings) -> None:
    """Route by event.type."""
    et = event["type"]
    data_object = event["data"]["object"]

    if et == "checkout.session.completed":
        _handle_checkout_session_completed(data_object, db, settings)
    elif et == "customer.subscription.updated":
        _handle_subscription_updated(data_object, db, settings)
    elif et == "customer.subscription.deleted":
        _handle_subscription_deleted(data_object, db, settings)
    elif et == "invoice.payment_failed":
        _handle_invoice_payment_failed(data_object, db, settings)
    else:
        logger.debug("stripe webhook unhandled event type: %s", et)


def _as_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        d = obj.to_dict()
        return d if isinstance(d, dict) else dict(obj)
    return dict(obj)


def _resolve_uid_from_session(session: dict[str, Any]) -> str | None:
    uid = session.get("client_reference_id")
    if isinstance(uid, str) and uid.strip():
        return uid.strip()
    meta = session.get("metadata") or {}
    if isinstance(meta, dict):
        m = meta.get("firebase_uid")
        if isinstance(m, str) and m.strip():
            return m.strip()
    return None


def _handle_checkout_session_completed(
    session: Any,
    db: Any,
    settings: Settings,
) -> None:
    s = _as_dict(session)
    if s.get("mode") != "subscription":
        logger.info("checkout.session.completed skipped: mode=%s", s.get("mode"))
        return

    uid = _resolve_uid_from_session(s)
    if not uid:
        logger.error("checkout.session.completed: missing client_reference_id / metadata.firebase_uid")
        return

    customer_id = s.get("customer")
    subscription_id = s.get("subscription")
    if not customer_id or not subscription_id:
        logger.error(
            "checkout.session.completed: missing customer or subscription session=%s",
            s.get("id"),
        )
        return

    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")

    if not isinstance(customer_id, str) or not isinstance(subscription_id, str):
        logger.error("checkout.session.completed: invalid customer/subscription types")
        return

    set_customer_uid_mapping(db, customer_id, uid)

    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        sub_dict = _as_dict(sub)
    except stripe.StripeError as e:
        logger.exception("Failed to retrieve subscription after checkout: %s", e)
        raise

    upsert_subscription_from_stripe_subscription(db, uid, customer_id, sub_dict, settings)


def _handle_subscription_updated(sub: Any, db: Any, settings: Settings) -> None:
    stripe_sub = _as_dict(sub)
    customer_id = stripe_sub.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    if not isinstance(customer_id, str):
        logger.error("customer.subscription.updated: missing customer id")
        return

    uid = get_uid_for_customer(db, customer_id)
    if not uid:
        logger.warning(
            "customer.subscription.updated: no uid mapping for customer=%s subscription=%s",
            customer_id,
            stripe_sub.get("id"),
        )
        return

    upsert_subscription_from_stripe_subscription(db, uid, customer_id, stripe_sub, settings)


def _handle_subscription_deleted(sub: Any, db: Any, settings: Settings) -> None:
    stripe_sub = _as_dict(sub)
    customer_id = stripe_sub.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    if not isinstance(customer_id, str):
        logger.error("customer.subscription.deleted: missing customer id")
        return

    uid = get_uid_for_customer(db, customer_id)
    if not uid:
        logger.warning(
            "customer.subscription.deleted: no uid mapping for customer=%s",
            customer_id,
        )
        return

    apply_subscription_deleted(db, uid, customer_id)


def _handle_invoice_payment_failed(invoice: Any, db: Any, settings: Settings) -> None:
    inv = _as_dict(invoice)
    customer_id = inv.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    subscription_id = inv.get("subscription")
    if isinstance(subscription_id, dict):
        subscription_id = subscription_id.get("id")

    if not isinstance(customer_id, str):
        logger.error("invoice.payment_failed: missing customer id")
        return

    uid = get_uid_for_customer(db, customer_id)
    if not uid:
        logger.warning("invoice.payment_failed: no uid mapping for customer=%s", customer_id)
        return

    if isinstance(subscription_id, str) and subscription_id:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            upsert_subscription_from_stripe_subscription(
                db, uid, customer_id, _as_dict(sub), settings
            )
        except stripe.StripeError as e:
            logger.exception("invoice.payment_failed: retrieve subscription: %s", e)
            raise
    else:
        logger.warning(
            "invoice.payment_failed: no subscription on invoice id=%s",
            inv.get("id"),
        )
