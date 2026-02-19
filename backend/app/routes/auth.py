from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/validate")
async def validate_token():
    """
    Validate token. Placeholder until Phase 1 (Firebase Auth).
    Frontend can call this to check auth status.
    """
    return {"status": "success", "message": "Auth placeholder - Firebase auth in Phase 1"}