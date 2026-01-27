from fastapi import Header, HTTPException, Depends
from typing import Annotated
from app.config import Settings

settings = Settings()

def get_access_token(
    x_access_token: Annotated[str | None, Header(alias="x-access-token")] = None
) -> str:
    """
    FastAPI dependency that validates and returns the access token.
    Use this in route handlers that require authentication.
    """
    if not x_access_token:
        raise HTTPException(status_code=401, detail="Missing access token")
    if x_access_token != settings.ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid access token")
    return x_access_token

