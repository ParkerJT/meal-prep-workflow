"""
Unit tests for web recipe extraction (LLM path is mocked).

Manual QA checklist (run against a running backend with OPENAI_API_KEY, e.g. POST /api/workflow/generate):
- Blog / magazine recipe with rich layout and schema (verify ingredients + steps complete).
- Minimal text-only recipe site (verify parsing still works).
- Long article with narrative before the recipe card (verify primary recipe is extracted).
- Page with "related recipes" or sidebar links (verify main recipe wins).
"""

from unittest.mock import MagicMock

from openai import OpenAI

from app.services.agents.extraction import (
  WEB_PAGE_TEXT_MAX_CHARS,
  extract_recipe_from_web_page,
)
from app.services.agents.models import Ingredient, OriginalRecipe


def test_extract_recipe_from_web_page_returns_parsed_recipe():
  expected = OriginalRecipe(
    title="Test Soup",
    description=None,
    servings=2,
    ingredients=[Ingredient(name="water", quantity=1, unit="cup")],
    instructions=["Boil gently."],
  )
  mock_response = MagicMock()
  mock_response.choices = [MagicMock()]
  mock_response.choices[0].message.parsed = expected

  mock_client = MagicMock(spec=OpenAI)
  mock_client.beta.chat.completions.parse.return_value = mock_response

  text = "Ingredients: 1 cup water. Instructions: Boil gently."
  out = extract_recipe_from_web_page(text, mock_client)

  assert out is expected
  mock_client.beta.chat.completions.parse.assert_called_once()
  kwargs = mock_client.beta.chat.completions.parse.call_args.kwargs
  assert kwargs["messages"][1]["role"] == "user"
  user_content = kwargs["messages"][1]["content"]
  assert "https://" not in user_content
  assert "1 cup water" in user_content
  assert kwargs["response_format"] is OriginalRecipe


def test_extract_recipe_from_web_page_truncates_long_content():
  expected = OriginalRecipe(
    title="Long",
    description=None,
    servings=1,
    ingredients=[Ingredient(name="x", quantity=1, unit=None)],
    instructions=["Do it."],
  )
  mock_response = MagicMock()
  mock_response.choices = [MagicMock()]
  mock_response.choices[0].message.parsed = expected

  mock_client = MagicMock(spec=OpenAI)
  mock_client.beta.chat.completions.parse.return_value = mock_response

  long_text = "a" * (WEB_PAGE_TEXT_MAX_CHARS + 500)
  extract_recipe_from_web_page(long_text, mock_client)

  user_content = mock_client.beta.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
  assert "[Content truncated for length.]" in user_content
  assert len(user_content) < len(long_text) + 200
