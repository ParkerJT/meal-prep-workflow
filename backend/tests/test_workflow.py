"""Tests for run_workflow orchestration and POST /api/workflow/generate."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.dependencies import require_subscription
from app.main import app
from app.services.agents.models import (
    ConvertedRecipe,
    ConversionMetadata,
    Ingredient,
    NutritionalInfo,
    OriginalRecipe,
    UserAdjustments,
    UserRequest,
)
from app.services.agents.workflow import run_workflow


def _sample_converted() -> ConvertedRecipe:
    return ConvertedRecipe(
        title="Soup",
        description=None,
        servings=2,
        ingredients=[Ingredient(name="water", quantity=2, unit="cup")],
        instructions=["Boil."],
        nutritional_info=NutritionalInfo(calories=100, protein=10),
        conversion_metadata=ConversionMetadata(
            original_recipe_url="https://example.com/r",
            conversion_notes="Scaled.",
        ),
    )


@patch("app.services.agents.workflow.get_firestore_client")
@patch("app.services.agents.workflow.convert_recipe")
@patch("app.services.agents.workflow.ensure_canonical_original_recipe")
@patch("app.services.agents.workflow.recipe_extraction_workflow")
def test_run_workflow_extracts_persists_converts(
    mock_extract: MagicMock,
    mock_ensure: MagicMock,
    mock_convert: MagicMock,
    mock_db: MagicMock,
) -> None:
    mock_db.return_value = MagicMock()
    original = OriginalRecipe(
        title="Soup",
        description=None,
        servings=4,
        ingredients=[Ingredient(name="water", quantity=4, unit="cup")],
        instructions=["Boil."],
    )
    converted = _sample_converted()
    mock_extract.return_value = original
    mock_convert.return_value = converted

    ur = UserRequest(
        recipe_url="https://example.com/r",
        user_adjustments=UserAdjustments(
            target_servings=2,
            target_calories=400,
            target_protein=30,
        ),
    )

    out = run_workflow(ur)

    assert out is converted
    mock_extract.assert_called_once()
    mock_ensure.assert_called_once()
    mock_convert.assert_called_once()


async def _override_require_subscription() -> dict:
    """Bypass Firestore subscription check in API tests."""
    return {"uid": "test-user", "email": "test@example.com"}


@patch("app.routes.workflow.run_workflow")
def test_workflow_generate_endpoint(mock_run: MagicMock) -> None:
    converted = _sample_converted()
    mock_run.return_value = converted

    app.dependency_overrides[require_subscription] = _override_require_subscription
    try:
        client = TestClient(app)
        resp = client.post(
            "/api/workflow/generate",
            json={
                "recipe_url": "https://example.com/r",
                "user_adjustments": {
                    "target_servings": 2,
                    "target_calories": 400,
                    "target_protein": 30,
                },
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Soup"
    mock_run.assert_called_once()
