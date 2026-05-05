from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_user_optional, get_firestore
from app.schemas.recipes import PaginatedPublishedResponse, PublishedRecipeDetail, PublishedRecipeSummary
from app.services.firestore import published as published_svc

router = APIRouter(prefix="/api/published-recipes", tags=["published-recipes"])


@router.get("", response_model=PaginatedPublishedResponse)
def list_published_recipes(
    db=Depends(get_firestore),
    current_user: dict | None = Depends(get_current_user_optional),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
):
    if cursor:
        try:
            published_svc.decode_cursor(cursor)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid cursor") from e
    rows, next_cursor = published_svc.list_published(
        db,
        limit=limit,
        cursor=cursor,
        exclude_owner_user_id=(current_user["uid"] if current_user else None),
    )
    items = [PublishedRecipeSummary(**r) for r in rows]
    return PaginatedPublishedResponse(items=items, next_cursor=next_cursor)


@router.get("/{owner_user_id}/{saved_recipe_id}", response_model=PublishedRecipeDetail)
def get_published_recipe(
    owner_user_id: str,
    saved_recipe_id: str,
    db=Depends(get_firestore),
):
    row = published_svc.get_published_detail(db, owner_user_id, saved_recipe_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Published recipe not found")
    return PublishedRecipeDetail(**row)
