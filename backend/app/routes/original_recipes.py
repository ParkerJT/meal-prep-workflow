from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_firestore
from app.services.agents.models import OriginalRecipeDocument
from app.services.firestore import original_recipes as original_svc

router = APIRouter(prefix="/api/original-recipes", tags=["original-recipes"])


@router.get("/{recipe_id}", response_model=OriginalRecipeDocument)
def get_original_recipe(
    recipe_id: str,
    _user: dict = Depends(get_current_user),
    db=Depends(get_firestore),
):
    doc = original_svc.get_original_recipe(db, recipe_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Original recipe not found")
    return doc


@router.put("/{recipe_id}", response_model=OriginalRecipeDocument)
def upsert_original_recipe(
    recipe_id: str,
    body: OriginalRecipeDocument,
    _user: dict = Depends(get_current_user),
    db=Depends(get_firestore),
):
    if body.id != recipe_id:
        raise HTTPException(
            status_code=400,
            detail="Document id must match path",
        )
    return original_svc.upsert_original_recipe(db, body)
