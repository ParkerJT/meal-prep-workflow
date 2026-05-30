from __future__ import annotations

from openai import OpenAI

from app.services.agents.llm_factory import get_conversion_model
from app.services.agents.models import ConvertedRecipe, OriginalRecipe, UserRequest

CONVERSION_MODEL = get_conversion_model()

SYSTEM_INSTRUCTIONS_CONVERSION = """You are a meal-prep recipe conversion specialist. You receive an extracted recipe and the user's target portion and nutrition goals. You must produce a converted recipe that matches the required output schema.

## Your task
1. **Servings**: Scale the recipe from the original `servings` count to the user's `target_servings`. Adjust every measurable ingredient quantity proportionally unless a different adjustment is clearly needed for food safety or practicality (e.g. whole eggs, single-use items)—if you change an amount for such reasons, explain briefly in `conversion_notes`.
2. **Instructions**: Update steps when needed so they remain accurate for the new amounts (e.g. pan sizes, "divide into N portions" where N is the new serving count). Preserve technique, times, and temperatures from the original unless scaling requires a small tweak.
3. **Title and description**: Keep the recipe identity; you may lightly edit the description to reflect the scaled batch if helpful.
4. **Nutrition (`nutritional_info`)**: Estimate **calories per serving** and **grams of protein per serving** for the **converted** recipe. Use reasonable culinary and nutrition judgment from the ingredients and cooking method. **Aim close to** the user's `target_calories` and `target_protein` per serving when feasible by adjusting lean proteins, fats, or starches in `conversion_notes`—do not invent impossible precision; round to whole numbers for calories and protein.
5. **Conversion notes (`conversion_metadata.conversion_notes`)**: Summarize what you scaled, any macro-focused tweaks, and notable estimation caveats. Do not claim laboratory accuracy for nutrition estimates.

## Output schema
You must output a complete `ConvertedRecipe` with:
- `title`, `description` (optional), `servings` (must equal `target_servings`)
- `ingredients` — scaled list with `name`, `quantity`, `unit`
- `instructions` — clear steps for the converted batch
- `nutritional_info` — `calories` and `protein` (integers, per serving)
- `conversion_metadata` — include `conversion_notes`; you may omit or placeholder `original_recipe_url` in your draft (the application will set the URL authoritatively).

## Quality
- Preserve the spirit and order of the original recipe.
- Use consistent units; prefer common cooking units (cups, tbsp, g, oz) over odd fractions when equivalent.
- If the original has ambiguous amounts, make a reasonable scaled estimate and note it in `conversion_notes`.
"""


def convert_recipe(
    original_recipe: OriginalRecipe,
    user_request: UserRequest,
    openai_client: OpenAI,
    *,
    source_url: str | None = None,
) -> ConvertedRecipe:
    """
    Convert an extracted recipe to the user's target servings and macro goals using structured LLM output.
    ``conversion_metadata.original_recipe_url`` is set from ``source_url`` or ``user_request.recipe_url``.
    """
    original_json = original_recipe.model_dump_json(indent=2)
    adjustments_json = user_request.user_adjustments.model_dump_json(indent=2)
    provenance = source_url or user_request.recipe_url or ""

    prompt = f"""## Original recipe (JSON)
{original_json}

## User targets (JSON)
{adjustments_json}

## Source URL (for context only; do not rely on fetching)
{provenance}

Produce the converted recipe as specified in the system instructions. Servings must equal target_servings. Estimate nutrition per serving for the converted recipe."""

    response = openai_client.beta.chat.completions.parse(
        model=CONVERSION_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS_CONVERSION},
            {"role": "user", "content": prompt},
        ],
        response_format=ConvertedRecipe,
    )

    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Conversion model returned no parsed ConvertedRecipe")

    return parsed.model_copy(
        update={
            "conversion_metadata": parsed.conversion_metadata.model_copy(
                update={"original_recipe_url": provenance},
            ),
        },
    )
