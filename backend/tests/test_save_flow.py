"""save_from_workflow orchestration."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.agents.models import Ingredient, OriginalRecipe, SavedRecipe
from app.services.save_flow import save_from_workflow


def test_save_from_workflow_creates_user_saved_recipe():
    original = OriginalRecipe(
        title="New Recipe",
        description=None,
        servings=2,
        ingredients=[Ingredient(name="x", quantity=1, unit=None)],
        instructions=["Mix."],
    )
    saved = SavedRecipe(
        saved_at=datetime.now(timezone.utc),
        notes="",
        source_url="https://example.com/r",
        source_type="web",
        original_recipe=original,
        converted_recipe=None,
    )

    with patch("app.services.save_flow.saved_svc.create_saved", return_value=("doc1", saved)) as mock_create:
        save_from_workflow(
            MagicMock(),
            "user-uid",
            source_url="https://example.com/r",
            source_type="web",
            original_recipe=original,
        )

    mock_create.assert_called_once()
    created = mock_create.call_args.args[2]
    assert created.original_recipe == original
    assert created.source_type == "web"
