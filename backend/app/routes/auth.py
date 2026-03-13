from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """
    Validate Firebase auth token. Frontend can call this to check auth status.
    """

    return {"status": "success", "message": "Auth successful", "user": current_user}