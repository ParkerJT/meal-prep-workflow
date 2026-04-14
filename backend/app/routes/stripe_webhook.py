"""
Stripe webhook endpoint. Verifies signatures per https://docs.stripe.com/webhooks/signatures
"""

from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, HTTPException, Request, Response

from app.config import Settings
from app.services.firestore.client import get_firestore_client
from app.services.stripe_webhook_handlers import handle_stripe_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["stripe"])
settings = Settings()


@router.post(
    "/stripe",
    summary="Stripe webhook",
    description="Receives Stripe events; verifies Stripe-Signature using STRIPE_WEBHOOK_SECRET.",
)
async def stripe_webhook(request: Request) -> Response:
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not set")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        logger.warning("stripe webhook invalid payload: %s", e)
        raise HTTPException(status_code=400, detail="Invalid payload") from e
    except stripe.SignatureVerificationError as e:
        logger.warning("stripe webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    try:
        db = get_firestore_client()
        handle_stripe_event(event, db, settings)
    except Exception as e:
        logger.exception("stripe webhook handler error for event %s", getattr(event, "id", "?"))
        raise HTTPException(status_code=500, detail="Webhook handler failed") from e

    return Response(status_code=200)
