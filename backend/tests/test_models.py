import pytest
from pydantic import ValidationError

from app.services.agents.models import UserAdjustments, UserRequest
from app.services.user_text import PERSONAL_INSTRUCTIONS_MAX_CHARS, RECIPE_TEXT_MAX_CHARS


def _adjustments() -> UserAdjustments:
    return UserAdjustments(
        target_servings=4,
        target_calories=500,
        target_protein=30,
    )


def test_user_request_rejects_oversize_recipe_text():
    with pytest.raises(ValidationError):
        UserRequest(
            input_mode="text",
            recipe_text="x" * (RECIPE_TEXT_MAX_CHARS + 1),
            user_adjustments=_adjustments(),
        )


def test_user_request_rejects_oversize_personal_instructions():
    with pytest.raises(ValidationError):
        UserRequest(
            recipe_url="https://example.com/recipe",
            personal_instructions="x" * (PERSONAL_INSTRUCTIONS_MAX_CHARS + 1),
            user_adjustments=_adjustments(),
        )


def test_user_request_sanitizes_and_accepts_valid_text_mode():
    req = UserRequest(
        input_mode="text",
        recipe_text="  Chicken soup\n2 cups broth  ",
        personal_instructions=" keep it low sodium ",
        user_adjustments=_adjustments(),
    )
    assert req.recipe_text == "Chicken soup\n2 cups broth"
    assert req.personal_instructions == "keep it low sodium"
