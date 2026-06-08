from fastapi import APIRouter, Depends

from app.dependencies import get_current_uid, get_firestore
from app.schemas.generation_preferences import (
    GenerationPreferencesResponse,
    GenerationPreferencesUpdate,
)
from app.services.firestore import generation_preferences as prefs_svc

router = APIRouter(
    prefix="/api/users/me/generation-preferences",
    tags=["generation-preferences"],
)


@router.get("", response_model=GenerationPreferencesResponse)
def get_my_generation_preferences(
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
) -> GenerationPreferencesResponse:
    return GenerationPreferencesResponse(
        global_instructions=prefs_svc.get_generation_preferences(db, uid),
    )


@router.patch("", response_model=GenerationPreferencesResponse)
def patch_my_generation_preferences(
    body: GenerationPreferencesUpdate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
) -> GenerationPreferencesResponse:
    saved = prefs_svc.set_generation_preferences(db, uid, body.global_instructions)
    return GenerationPreferencesResponse(global_instructions=saved)
