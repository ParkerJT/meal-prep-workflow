"""Pasted text extraction helper."""

from unittest.mock import MagicMock, patch

from openai import OpenAI

from app.services.agents.extraction import extract_recipe_from_pasted_text
from app.services.agents.models import Ingredient, OriginalRecipe


@patch("app.services.agents.extraction.EXTRACTION_MODEL", "gpt-4o-mini")
def test_extract_recipe_from_pasted_text_returns_parsed_recipe():
    client = MagicMock(spec=OpenAI)
    parsed = OriginalRecipe(
        title="Soup",
        description=None,
        servings=2,
        ingredients=[Ingredient(name="water", quantity=2, unit="cup")],
        instructions=["Boil."],
    )
    client.beta.chat.completions.parse.return_value.choices = [
        MagicMock(message=MagicMock(parsed=parsed))
    ]

    out = extract_recipe_from_pasted_text("Boil 2 cups water.", client)

    assert out.title == "Soup"
    client.beta.chat.completions.parse.assert_called_once()
