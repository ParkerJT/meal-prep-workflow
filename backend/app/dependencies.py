"""
Firebase auth dependencies.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

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

