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
from app.services.firestore import original_recipes as original_svc
from app.services.firestore import saved_recipes as saved_svc
from app.services.firestore.timestamps import utc_now
from app.services.recipe_id import compute_recipe_id, normalize_source_url

router = APIRouter(prefix="/api/users/me/saved-recipes", tags=["saved-recipes"])


def _to_response(doc_id: str, sr: SavedRecipe) -> SavedRecipeResponse:
    return SavedRecipeResponse(
        id=doc_id,
        recipe_id=sr.recipe_id,
        saved_at=sr.saved_at,
        notes=sr.notes,
        converted_recipe=sr.converted_recipe,
        published=sr.published,
        copied_from_user_id=sr.copied_from_user_id,
        copied_from_saved_recipe_id=sr.copied_from_saved_recipe_id,
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
        published=body.published,
    )
    return _to_response(doc_id, sr)


@router.post("/from-generate", response_model=SavedRecipeResponse, status_code=201)
def create_saved_from_generate(
    body: GeneratedSaveCreate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    normalized = normalize_source_url(body.source_url)
    recipe_id = compute_recipe_id(normalized)
    if original_svc.get_original_recipe(db, recipe_id) is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Canonical original recipe not found for source_url. "
                "Run /api/workflow/generate first and retry save."
            ),
        )

    recipe = SavedRecipe(
        recipe_id=recipe_id,
        saved_at=utc_now(),
        notes=body.notes,
        converted_recipe=body.converted_recipe,
        published=body.published,
        copied_from_user_id=None,
        copied_from_saved_recipe_id=None,
    )
    doc_id, sr = saved_svc.create_saved(db, uid, recipe)
    return _to_response(doc_id, sr)


@router.post("", response_model=SavedRecipeResponse, status_code=201)
def create_my_saved_recipe(
    body: SavedRecipeCreate,
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
):
    if body.source_owner_user_id and body.source_saved_recipe_id:
        try:
            doc_id, sr = saved_svc.copy_from_published(
                db,
                uid,
                source_owner_user_id=body.source_owner_user_id,
                source_saved_recipe_id=body.source_saved_recipe_id,
                notes=body.notes,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _to_response(doc_id, sr)

    assert body.recipe_id is not None
    recipe = SavedRecipe(
        recipe_id=body.recipe_id,
        saved_at=utc_now(),
        notes=body.notes,
        converted_recipe=body.converted_recipe,
        published=body.published,
        copied_from_user_id=None,
        copied_from_saved_recipe_id=None,
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
    try:
        row = saved_svc.patch_saved(
            db,
            uid,
            saved_recipe_id,
            notes=body.notes,
            converted_recipe=body.converted_recipe,
            published=body.published,
            recipe_id=body.recipe_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
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
