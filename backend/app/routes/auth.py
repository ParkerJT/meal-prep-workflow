from fastapi import APIRouter, Depends
from app.dependencies import get_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/validate")
async def validate_token(
    access_token: str = Depends(get_access_token)
):
    """
    Validate access token from the x-access-token header.
    This endpoint exists for frontend to check token validity.
    """
    return {"status": "success", "message": "Access token validated"}