"""Tests for generation preferences API."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.dependencies import get_current_uid, get_firestore
from app.main import app


def _override_uid() -> str:
    return "test-user"


def _override_db():
    return MagicMock()


@patch("app.routes.generation_preferences.prefs_svc.get_generation_preferences", return_value="vegetarian")
def test_get_generation_preferences(mock_get: MagicMock) -> None:
    app.dependency_overrides[get_current_uid] = _override_uid
    app.dependency_overrides[get_firestore] = _override_db
    try:
        client = TestClient(app)
        resp = client.get("/api/users/me/generation-preferences")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["global_instructions"] == "vegetarian"
    mock_get.assert_called_once()


@patch(
    "app.routes.generation_preferences.prefs_svc.set_generation_preferences",
    return_value="low carb",
)
def test_patch_generation_preferences(mock_set: MagicMock) -> None:
    app.dependency_overrides[get_current_uid] = _override_uid
    app.dependency_overrides[get_firestore] = _override_db
    try:
        client = TestClient(app)
        resp = client.patch(
            "/api/users/me/generation-preferences",
            json={"global_instructions": "low carb"},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["global_instructions"] == "low carb"
    mock_set.assert_called_once()


def test_patch_rejects_oversize_global_instructions() -> None:
    app.dependency_overrides[get_current_uid] = _override_uid
    app.dependency_overrides[get_firestore] = _override_db
    try:
        client = TestClient(app)
        resp = client.patch(
            "/api/users/me/generation-preferences",
            json={"global_instructions": "x" * 1001},
        )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 422
