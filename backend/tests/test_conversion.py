"""Unit tests for recipe conversion (LLM path is mocked)."""

from unittest.mock import MagicMock

import pytest
from openai import OpenAI

from app.services.agents.conversion import convert_recipe
from app.services.agents.models import (
    ConvertedRecipe,
    ConversionMetadata,
    Ingredient,
    NutritionalInfo,
    OriginalRecipe,
    UserAdjustments,
    UserRequest,
)


def test_convert_recipe_returns_parsed_and_sets_metadata_url():
    wrong_url = "https://wrong.example/recipe"
    user_request = UserRequest(
        recipe_url="https://example.com/recipe",
        user_adjustments=UserAdjustments(
            target_servings=4,
            target_calories=500,
            target_protein=40,
        ),
    )
    original = OriginalRecipe(
        title="Test Chili",
        description="Spicy",
        servings=2,
        ingredients=[
            Ingredient(name="beans", quantity=1, unit="can"),
        ],
        instructions=["Simmer."],
    )
    parsed_from_llm = ConvertedRecipe(
        title="Test Chili",
        description="Spicy",
        servings=4,
        ingredients=[Ingredient(name="beans", quantity=2, unit="can")],
        instructions=["Simmer."],
        nutritional_info=NutritionalInfo(calories=500, protein=40),
        conversion_metadata=ConversionMetadata(
            original_recipe_url=wrong_url,
            conversion_notes="Scaled from 2 to 4 servings.",
        ),
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = parsed_from_llm

    mock_client = MagicMock(spec=OpenAI)
    mock_client.beta.chat.completions.parse.return_value = mock_response

    out = convert_recipe(original, user_request, mock_client)

    assert out.conversion_metadata.original_recipe_url == user_request.recipe_url
    assert out.conversion_metadata.original_recipe_url != wrong_url
    assert out.conversion_metadata.conversion_notes == parsed_from_llm.conversion_metadata.conversion_notes

    mock_client.beta.chat.completions.parse.assert_called_once()
    kwargs = mock_client.beta.chat.completions.parse.call_args.kwargs
    assert kwargs["response_format"] is ConvertedRecipe
    assert kwargs["messages"][0]["role"] == "system"
    assert "meal-prep" in kwargs["messages"][0]["content"].lower()
    user_content = kwargs["messages"][1]["content"]
    assert user_request.recipe_url in user_content
    assert "target_servings" in user_content
    assert "Test Chili" in user_content


def test_convert_recipe_raises_when_parse_returns_none():
    user_request = UserRequest(
        recipe_url="https://example.com/r",
        user_adjustments=UserAdjustments(
            target_servings=1,
            target_calories=300,
            target_protein=20,
        ),
    )
    original = OriginalRecipe(
        title="X",
        description=None,
        servings=1,
        ingredients=[Ingredient(name="a", quantity=1, unit=None)],
        instructions=["Go."],
    )
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = None

    mock_client = MagicMock(spec=OpenAI)
    mock_client.beta.chat.completions.parse.return_value = mock_response

    with pytest.raises(ValueError, match="no parsed"):
        convert_recipe(original, user_request, mock_client)
