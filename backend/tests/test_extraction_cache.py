"""Cache hit on original_recipes skips expensive extraction paths."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.agents.extraction import recipe_extraction_workflow
from app.services.agents.models import Ingredient, OriginalRecipeDocument


@pytest.fixture
def sample_document() -> OriginalRecipeDocument:
    return OriginalRecipeDocument(
        id="a" * 32,
        title="Cached Soup",
        description=None,
        servings=4,
        ingredients=[Ingredient(name="water", quantity=1, unit="cup")],
        instructions=["Boil."],
        source_url="https://example.com/soup",
        source_type="web",
        created_at=datetime.now(timezone.utc),
        created_by="uid1",
    )


@patch("app.services.agents.extraction.scrape_youtube_video")
@patch("app.services.agents.extraction.scrape_web_page")
@patch("app.services.agents.extraction.get_original_recipe")
def test_cache_hit_skips_youtube_and_web(
    mock_get_original,
    mock_scrape_web,
    mock_scrape_youtube,
    sample_document: OriginalRecipeDocument,
):
    mock_get_original.return_value = sample_document
    db = MagicMock()

    out = recipe_extraction_workflow(db, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    mock_scrape_youtube.assert_not_called()
    mock_scrape_web.assert_not_called()
    assert out.title == "Cached Soup"
    assert out.servings == 4
