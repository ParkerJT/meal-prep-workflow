"""Orchestrate original_recipes + saved_recipes for workflow saves (BUILD_PLAN §2.4)."""

from __future__ import annotations

from typing import Any, Literal

from app.services.agents.models import ConvertedRecipe, OriginalRecipe, OriginalRecipeDocument, SavedRecipe
from app.services.firestore import original_recipes as original_svc
from app.services.firestore import saved_recipes as saved_svc
from app.services.firestore.timestamps import utc_now
from app.services.recipe_id import compute_recipe_id, normalize_source_url

def infer_source_type(url: str) -> Literal["web", "youtube"]:
    """Match extraction routing: YouTube hosts vs everything else we treat as web."""
    if url.startswith("https://www.youtube.com") or url.startswith("https://youtu.be"):
        return "youtube"
    return "web"


def ensure_canonical_original_recipe(
    db: Any,
    *,
    source_url: str,
    original_recipe: OriginalRecipe,
    created_by: str | None = None,
    source_type: Literal["web", "youtube"] | None = None,
) -> None:
    """
    Create ``original_recipes/{recipe_id}`` on miss only (no overwrite on hit).
    Used after generate/extraction so LLM extraction cost is retained (§2.5.3).
    """
    normalized = normalize_source_url(source_url)
    original_recipe_id = compute_recipe_id(normalized)
    if original_svc.get_original_recipe(db, original_recipe_id) is not None:
        return
    st = source_type if source_type is not None else infer_source_type(source_url)
    doc = OriginalRecipeDocument(
        id=original_recipe_id,
        title=original_recipe.title,
        description=original_recipe.description,
        servings=original_recipe.servings,
        ingredients=original_recipe.ingredients,
        instructions=original_recipe.instructions,
        source_url=normalized,
        source_type=st,
        created_at=utc_now(),
        created_by=created_by,
    )
    original_svc.upsert_original_recipe(db, doc)


def save_from_workflow(
    db: Any,
    uid: str,
    *,
    source_url: str,
    source_type: Literal["web", "youtube"],
    original_recipe: OriginalRecipe,
    converted_recipe: ConvertedRecipe | None = None,
    notes: str = "",
) -> tuple[str, SavedRecipe]:
    """
    Ensure canonical ``original_recipes/{recipe_id}`` exists (create on miss only), then
    append a ``saved_recipes`` row for ``uid``.
    """
    normalized = normalize_source_url(source_url)
    recipe_id = compute_recipe_id(normalized)

    ensure_canonical_original_recipe(
        db,
        source_url=source_url,
        original_recipe=original_recipe,
        created_by=uid,
        source_type=source_type,
    )

    sr = SavedRecipe(
        original_recipe_id=recipe_id,
        saved_at=utc_now(),
        notes=notes,
        converted_recipe=converted_recipe,
    )
    return saved_svc.create_saved(db, uid, sr)
