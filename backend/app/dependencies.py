"""
Firebase auth dependencies.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

from app.services.firestore.client import get_firestore_client
from app.services.firestore.subscription import get_subscription

# Extract Bearer token from request and handle error manually if missing
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):
    """
    Get the current user from the token (for endpoints that require authentication)
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token # Returns a dict with user info
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):
    """
    Get the current user from the token (optional for endpoints that don't require authentication)
    """
    if credentials is None:
        return None
    
    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token # Returns a dict with user info
    except auth.InvalidIdTokenError:
        return None # Don't raise, just move on and return None


def get_firestore():
    """Firestore client (requires Firebase Admin initialized at app startup)."""
    return get_firestore_client()


def get_current_uid(current_user: dict = Depends(get_current_user)) -> str:
    return current_user["uid"]


async def require_subscription(
    current_user: dict = Depends(get_current_user),
    db: Any = Depends(get_firestore),
) -> dict:
    """Allow only users with active paid status or an unexpired trial."""
    uid = current_user["uid"]
    sub = get_subscription(db, uid)
    allowed = False
    if sub is not None:
        if sub.status == "active":
            allowed = True
        elif sub.status == "trialing" and sub.trial_end is not None:
            allowed = sub.trial_end > datetime.now(timezone.utc)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "subscription_required",
                "message": "An active or trialing subscription is required for this feature.",
            },
        )
    return current_user

