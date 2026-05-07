"""save_from_workflow orchestration."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.agents.models import Ingredient, OriginalRecipe, SavedRecipe
from app.services.save_flow import save_from_workflow


def test_save_from_workflow_calls_upsert_when_no_original():
    original = OriginalRecipe(
        title="New Recipe",
        description=None,
        servings=2,
        ingredients=[Ingredient(name="x", quantity=1, unit=None)],
        instructions=["Mix."],
    )
    saved = SavedRecipe(
        original_recipe_id="rid",
        saved_at=datetime.now(timezone.utc),
        notes="",
        converted_recipe=None,
    )

    with (
        patch("app.services.save_flow.original_svc.get_original_recipe", return_value=None),
        patch("app.services.save_flow.original_svc.upsert_original_recipe") as mock_upsert,
        patch("app.services.save_flow.saved_svc.create_saved", return_value=("doc1", saved)) as mock_create,
    ):
        save_from_workflow(
            MagicMock(),
            "user-uid",
            source_url="https://example.com/r",
            source_type="web",
            original_recipe=original,
        )

    mock_upsert.assert_called_once()
    mock_create.assert_called_once()


def test_save_from_workflow_skips_upsert_when_original_exists():
    original = OriginalRecipe(
        title="New Recipe",
        description=None,
        servings=2,
        ingredients=[Ingredient(name="x", quantity=1, unit=None)],
        instructions=["Mix."],
    )
    saved = SavedRecipe(
        original_recipe_id="rid",
        saved_at=datetime.now(timezone.utc),
        notes="",
        converted_recipe=None,
    )
    existing = MagicMock()

    with (
        patch("app.services.save_flow.original_svc.get_original_recipe", return_value=existing),
        patch("app.services.save_flow.original_svc.upsert_original_recipe") as mock_upsert,
        patch("app.services.save_flow.saved_svc.create_saved", return_value=("doc1", saved)),
    ):
        save_from_workflow(
            MagicMock(),
            "user-uid",
            source_url="https://example.com/r",
            source_type="web",
            original_recipe=original,
        )

    mock_upsert.assert_not_called()
