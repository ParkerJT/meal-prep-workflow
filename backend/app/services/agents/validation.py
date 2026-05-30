from __future__ import annotations

from typing import Literal

from openai import OpenAI
from pydantic import BaseModel

from app.services.agents.llm_factory import get_extraction_model
from app.services.agents.models import ConvertedRecipe, OriginalRecipe, UserAdjustments

SYSTEM_INSTRUCTIONS_EXTRACTION_VALIDATOR = """You are a recipe input validator. You receive raw source content and a structured recipe extraction.

Your job is to decide whether the source reasonably represents a food recipe suitable for meal-prep conversion.

Reject when:
- The content is clearly not a recipe (news, spam, unrelated text, empty marketing copy).
- The content is inappropriate or unsafe to treat as a cooking recipe.
- The extraction is too incomplete to be useful (no real ingredients or no meaningful steps).

Do not invent recipe content. Base your decision only on the provided source snippet and extracted JSON."""


class ExtractionValidationResult(BaseModel):
    is_valid_recipe: bool
    rejection_code: Literal["not_a_recipe", "inappropriate_content", "extraction_incomplete"] | None = None
    message: str


def validate_extraction_programmatic(original: OriginalRecipe) -> str | None:
    if not original.title or not original.title.strip():
        return "Extracted recipe is missing a title."
    if len(original.ingredients) < 1:
        return "Extracted recipe has no ingredients."
    if len(original.instructions) < 1:
        return "Extracted recipe has no instructions."
    return None


def validate_extraction_with_llm(
    *,
    raw_content_snippet: str,
    original_recipe: OriginalRecipe,
    openai_client: OpenAI,
) -> ExtractionValidationResult:
    prompt = f"""## Source snippet (truncated)
{raw_content_snippet}

## Extracted recipe (JSON)
{original_recipe.model_dump_json(indent=2)}

Decide if this is a valid recipe extraction."""

    response = openai_client.beta.chat.completions.parse(
        model=get_extraction_model(),
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS_EXTRACTION_VALIDATOR},
            {"role": "user", "content": prompt},
        ],
        response_format=ExtractionValidationResult,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        return ExtractionValidationResult(
            is_valid_recipe=False,
            rejection_code="extraction_incomplete",
            message="Could not validate the extracted recipe.",
        )
    return parsed


def validate_conversion_programmatic(
    converted: ConvertedRecipe,
    user_adjustments: UserAdjustments,
) -> str | None:
    if converted.servings != user_adjustments.target_servings:
        return "Converted recipe servings do not match the requested target."
    if len(converted.ingredients) < 1:
        return "Converted recipe has no ingredients."
    if len(converted.instructions) < 1:
        return "Converted recipe has no instructions."
    calories = converted.nutritional_info.calories
    protein = converted.nutritional_info.protein
    if calories <= 0 or calories > 5000:
        return "Converted recipe has unrealistic calorie estimate."
    if protein < 0 or protein > 5000:
        return "Converted recipe has unrealistic protein estimate."
    return None
