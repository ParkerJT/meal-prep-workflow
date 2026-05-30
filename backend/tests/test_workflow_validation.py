"""Validation helpers for workflow nodes."""

from unittest.mock import MagicMock, patch

from openai import OpenAI

from app.services.agents.models import Ingredient, OriginalRecipe, UserAdjustments
from app.services.agents.validation import (
    ExtractionValidationResult,
    validate_conversion_programmatic,
    validate_extraction_programmatic,
    validate_extraction_with_llm,
)
from app.services.agents.models import (
    ConvertedRecipe,
    ConversionMetadata,
    NutritionalInfo,
)


def test_validate_extraction_programmatic_requires_ingredients():
    original = OriginalRecipe(
        title="Soup",
        description=None,
        servings=2,
        ingredients=[],
        instructions=["Boil."],
    )
    assert validate_extraction_programmatic(original) is not None


def test_validate_conversion_programmatic_checks_servings():
    converted = ConvertedRecipe(
        title="Soup",
        description=None,
        servings=4,
        ingredients=[Ingredient(name="water", quantity=2, unit="cup")],
        instructions=["Boil."],
        nutritional_info=NutritionalInfo(calories=100, protein=10),
        conversion_metadata=ConversionMetadata(
            original_recipe_url="https://example.com/r",
            conversion_notes="Scaled.",
        ),
    )
    adjustments = UserAdjustments(target_servings=2, target_calories=400, target_protein=30)
    assert validate_conversion_programmatic(converted, adjustments) is not None


@patch("app.services.agents.validation.get_extraction_model", return_value="gpt-4o-mini")
def test_validate_extraction_with_llm_parses_result(_mock_model: MagicMock):
    client = MagicMock(spec=OpenAI)
    parsed = ExtractionValidationResult(
        is_valid_recipe=False,
        rejection_code="not_a_recipe",
        message="This content is not a recipe.",
    )
    client.beta.chat.completions.parse.return_value.choices = [
        MagicMock(message=MagicMock(parsed=parsed))
    ]
    original = OriginalRecipe(
        title="Soup",
        description=None,
        servings=2,
        ingredients=[Ingredient(name="water", quantity=2, unit="cup")],
        instructions=["Boil."],
    )
    result = validate_extraction_with_llm(
        raw_content_snippet="some text",
        original_recipe=original,
        openai_client=client,
    )
    assert result.is_valid_recipe is False
    assert result.rejection_code == "not_a_recipe"
