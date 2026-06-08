import pytest

from app.services.recipe_id import compute_recipe_id, normalize_source_key, normalize_source_url


def test_normalize_strips_trailing_slash_and_fragment():
    a = normalize_source_url("HTTPS://Example.COM/path/to/recipe/")
    b = normalize_source_url("https://example.com/path/to/recipe#section")
    assert a == b == "https://example.com/path/to/recipe"


def test_normalize_drops_default_https_port():
    assert (
        normalize_source_url("https://example.com:443/foo")
        == "https://example.com/foo"
    )


def test_normalize_root_path():
    assert normalize_source_url("https://example.com/") == "https://example.com/"


def test_compute_recipe_id_deterministic():
    n = normalize_source_url("https://example.com/recipe")
    assert compute_recipe_id(n) == compute_recipe_id(n)
    assert len(compute_recipe_id(n)) == 32


def test_empty_url_raises():
    with pytest.raises(ValueError, match="empty"):
        normalize_source_url("   ")


def test_normalize_source_key_text_scheme():
    key = "text://550E8400-E29B-41D4-A716-446655440000"
    assert (
        normalize_source_key(key)
        == "text://550e8400-e29b-41d4-a716-446655440000"
    )


def test_normalize_source_key_rejects_invalid_text_uuid():
    with pytest.raises(ValueError, match="Invalid text source key"):
        normalize_source_key("text://not-a-uuid")
