"""Orchestrate user saved_recipes for workflow saves."""

from __future__ import annotations

from typing import Any, Literal

from app.services.agents.models import ConvertedRecipe, OriginalRecipe, SavedRecipe
from app.services.firestore import saved_recipes as saved_svc
from app.services.firestore.timestamps import utc_now
from app.services.recipe_id import normalize_source_url


def infer_source_type(url: str) -> Literal["web", "youtube"]:
    """Match extraction routing: YouTube hosts vs everything else we treat as web."""
    if url.startswith("https://www.youtube.com") or url.startswith("https://youtu.be"):
        return "youtube"
    return "web"


def save_from_workflow(
    db: Any,
    uid: str,
    *,
    source_url: str | None,
    source_type: Literal["web", "youtube", "text"],
    original_recipe: OriginalRecipe,
    converted_recipe: ConvertedRecipe | None = None,
    notes: str = "",
) -> tuple[str, SavedRecipe]:
    """Create a user-owned saved_recipes row with embedded recipe snapshots."""
    normalized = normalize_source_url(source_url) if source_url else None
    sr = SavedRecipe(
        saved_at=utc_now(),
        notes=notes,
        source_url=normalized,
        source_type=source_type,
        original_recipe=original_recipe,
        converted_recipe=converted_recipe,
    )
    return saved_svc.create_saved(db, uid, sr)
