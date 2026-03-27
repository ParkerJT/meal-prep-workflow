"""Orchestrate original_recipes + saved_recipes for workflow saves (BUILD_PLAN §2.4)."""

from __future__ import annotations

from typing import Any, Literal

from app.services.agents.models import ConvertedRecipe, OriginalRecipe, OriginalRecipeDocument, SavedRecipe
from app.services.firestore import original_recipes as original_svc
from app.services.firestore import saved_recipes as saved_svc
from app.services.firestore.timestamps import utc_now
from app.services.recipe_id import compute_recipe_id, normalize_source_url


def save_from_workflow(
    db: Any,
    uid: str,
    *,
    source_url: str,
    source_type: Literal["web", "youtube"],
    original_recipe: OriginalRecipe,
    converted_recipe: ConvertedRecipe | None = None,
    notes: str = "",
    published: bool = False,
) -> tuple[str, SavedRecipe]:
    """
    Ensure canonical ``original_recipes/{recipe_id}`` exists (create on miss only), then
    append a ``saved_recipes`` row for ``uid``.
    """
    normalized = normalize_source_url(source_url)
    recipe_id = compute_recipe_id(normalized)

    existing = original_svc.get_original_recipe(db, recipe_id)
    if existing is None:
        doc = OriginalRecipeDocument(
            id=recipe_id,
            title=original_recipe.title,
            description=original_recipe.description,
            servings=original_recipe.servings,
            ingredients=original_recipe.ingredients,
            instructions=original_recipe.instructions,
            source_url=normalized,
            source_type=source_type,
            created_at=utc_now(),
            created_by=uid,
        )
        original_svc.upsert_original_recipe(db, doc)

    sr = SavedRecipe(
        recipe_id=recipe_id,
        saved_at=utc_now(),
        notes=notes,
        converted_recipe=converted_recipe,
        published=published,
        copied_from_user_id=None,
        copied_from_saved_recipe_id=None,
    )
    return saved_svc.create_saved(db, uid, sr)
