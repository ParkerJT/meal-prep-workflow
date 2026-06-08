"""Tests for run_workflow orchestration and POST /api/workflow/generate."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.dependencies import get_current_uid, get_firestore, require_subscription
from app.services.agents.workflow import resolve_input_node
from app.main import app
from app.services.agents.errors import WorkflowRejection
from app.services.agents.models import (
    ConvertedRecipe,
    ConversionMetadata,
    GenerateResponse,
    Ingredient,
    NutritionalInfo,
    OriginalRecipe,
    UserAdjustments,
    UserRequest,
)
from app.services.agents.workflow import run_workflow


def _sample_original() -> OriginalRecipe:
    return OriginalRecipe(
        title="Soup",
        description=None,
        servings=4,
        ingredients=[Ingredient(name="water", quantity=4, unit="cup")],
        instructions=["Boil."],
    )


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


def _sample_generate_response() -> GenerateResponse:
    return GenerateResponse(
        original_recipe=_sample_original(),
        converted_recipe=_sample_converted(),
        source_url="https://example.com/r",
        source_type="web",
    )


@patch("app.services.agents.workflow._compiled_graph")
def test_run_workflow_returns_generate_response(mock_graph: MagicMock) -> None:
    mock_graph.invoke.return_value = {
        "original_recipe": _sample_original(),
        "converted_recipe": _sample_converted(),
        "source_url": "https://example.com/r",
        "source_type": "web",
    }

    ur = UserRequest(
        recipe_url="https://example.com/r",
        user_adjustments=UserAdjustments(
            target_servings=2,
            target_calories=400,
            target_protein=30,
        ),
    )

    out = run_workflow(ur)

    assert out.converted_recipe.title == "Soup"
    assert out.original_recipe.servings == 4
    mock_graph.invoke.assert_called_once()


@patch("app.services.agents.workflow._compiled_graph")
def test_run_workflow_raises_on_rejection(mock_graph: MagicMock) -> None:
    mock_graph.invoke.return_value = {
        "rejection": {"code": "not_a_recipe", "message": "This is not a recipe."},
    }

    ur = UserRequest(
        recipe_url="https://example.com/r",
        user_adjustments=UserAdjustments(
            target_servings=2,
            target_calories=400,
            target_protein=30,
        ),
    )

    try:
        run_workflow(ur)
        raise AssertionError("expected WorkflowRejection")
    except WorkflowRejection as exc:
        assert exc.code == "not_a_recipe"


async def _override_require_subscription() -> dict:
    """Bypass Firestore subscription check in API tests."""
    return {"uid": "test-user", "email": "test@example.com"}


def _override_uid() -> str:
    return "test-user"


def _override_db():
    return MagicMock()


def test_resolve_input_text_mode_sets_text_source_url() -> None:
    ur = UserRequest(
        input_mode="text",
        recipe_text="Chicken Soup\n2 cups broth",
        user_adjustments=UserAdjustments(
            target_servings=2,
            target_calories=400,
            target_protein=30,
        ),
    )
    out = resolve_input_node({"user_request": ur})
    assert out["source_type"] == "text"
    assert out["source_url"].startswith("text://")
    assert out["raw_content"] == "Chicken Soup\n2 cups broth"


@patch("app.routes.workflow.prefs_svc.get_generation_preferences", return_value="")
@patch("app.routes.workflow.run_workflow")
def test_workflow_generate_endpoint(mock_run: MagicMock, _mock_prefs: MagicMock) -> None:
    response = _sample_generate_response()
    mock_run.return_value = response

    app.dependency_overrides[require_subscription] = _override_require_subscription
    app.dependency_overrides[get_current_uid] = _override_uid
    app.dependency_overrides[get_firestore] = _override_db
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
    assert data["converted_recipe"]["title"] == "Soup"
    assert data["original_recipe"]["title"] == "Soup"
    mock_run.assert_called_once()


@patch("app.routes.workflow.prefs_svc.get_generation_preferences", return_value="")
@patch("app.routes.workflow.run_workflow")
def test_workflow_generate_returns_422_on_rejection(mock_run: MagicMock, _mock_prefs: MagicMock) -> None:
    mock_run.side_effect = WorkflowRejection("not_a_recipe", "This is not a recipe.")

    app.dependency_overrides[require_subscription] = _override_require_subscription
    app.dependency_overrides[get_current_uid] = _override_uid
    app.dependency_overrides[get_firestore] = _override_db
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

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "not_a_recipe"
