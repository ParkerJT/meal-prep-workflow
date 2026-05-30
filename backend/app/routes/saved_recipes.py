from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_uid, get_firestore
from app.schemas.recipes import (
    GeneratedSaveCreate,
    SavedRecipeCreate,
    SavedRecipeResponse,
    SavedRecipeUpdate,
    WorkflowSaveCreate,
)
from app.services.agents.models import SavedRecipe
from app.services import save_flow
from app.services.firestore import saved_recipes as saved_svc
from app.services.firestore.timestamps import utc_now
from app.services.recipe_id import normalize_source_url

router = APIRouter(prefix="/api/users/me/saved-recipes", tags=["saved-recipes"])


def _to_response(doc_id: str, sr: SavedRecipe) -> SavedRecipeResponse:
    return SavedRecipeResponse(
        id=doc_id,
        saved_at=sr.saved_at,
        notes=sr.notes,
        source_url=sr.source_url,
        source_type=sr.source_type,
        original_recipe=sr.original_recipe,
        converted_recipe=sr.converted_recipe,
    )


@router.get("", response_model=list[SavedRecipeResponse])
def list_my_saved_recipes(
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    rows = saved_svc.list_saved(db, uid)
    return [_to_response(i, sr) for i, sr in rows]


@router.get("/{saved_recipe_id}", response_model=SavedRecipeResponse)
def get_my_saved_recipe(
    saved_recipe_id: str,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    row = saved_svc.get_saved(db, uid, saved_recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Saved recipe not found")
    doc_id, sr = row
    return _to_response(doc_id, sr)


@router.post("/from-workflow", response_model=SavedRecipeResponse, status_code=201)
def create_saved_from_workflow(
    body: WorkflowSaveCreate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    doc_id, sr = save_flow.save_from_workflow(
        db,
        uid,
        source_url=body.source_url,
        source_type=body.source_type,
        original_recipe=body.original_recipe,
        converted_recipe=body.converted_recipe,
        notes=body.notes,
    )
    return _to_response(doc_id, sr)


@router.post("/from-generate", response_model=SavedRecipeResponse, status_code=201)
def create_saved_from_generate(
    body: GeneratedSaveCreate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    normalized = normalize_source_url(body.source_url) if body.source_url else None
    recipe = SavedRecipe(
        saved_at=utc_now(),
        notes=body.notes,
        source_url=normalized,
        source_type=body.source_type,
        original_recipe=body.original_recipe,
        converted_recipe=body.converted_recipe,
    )
    doc_id, sr = saved_svc.create_saved(db, uid, recipe)
    return _to_response(doc_id, sr)


@router.post("", response_model=SavedRecipeResponse, status_code=201)
def create_my_saved_recipe(
    body: SavedRecipeCreate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    normalized = normalize_source_url(body.source_url) if body.source_url else None
    recipe = SavedRecipe(
        saved_at=utc_now(),
        notes=body.notes,
        source_url=normalized,
        source_type=body.source_type,
        original_recipe=body.original_recipe,
        converted_recipe=body.converted_recipe,
    )
    doc_id, sr = saved_svc.create_saved(db, uid, recipe)
    return _to_response(doc_id, sr)


@router.patch("/{saved_recipe_id}", response_model=SavedRecipeResponse)
def patch_my_saved_recipe(
    saved_recipe_id: str,
    body: SavedRecipeUpdate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    row = saved_svc.patch_saved(
        db,
        uid,
        saved_recipe_id,
        notes=body.notes,
        converted_recipe=body.converted_recipe,
        original_recipe=body.original_recipe,
        source_url=body.source_url,
        source_type=body.source_type,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Saved recipe not found")
    doc_id, sr = row
    return _to_response(doc_id, sr)


@router.delete("/{saved_recipe_id}", status_code=204)
def delete_my_saved_recipe(
    saved_recipe_id: str,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    ok = saved_svc.delete_saved(db, uid, saved_recipe_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Saved recipe not found")
    return None
