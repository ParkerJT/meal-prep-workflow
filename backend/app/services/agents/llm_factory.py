from __future__ import annotations

from openai import OpenAI

from app.config import Settings

_settings = Settings()


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=_settings.OPENAI_API_KEY)


def get_extraction_model() -> str:
    return _settings.OPENAI_MODEL


def get_conversion_model() -> str:
    return _settings.OPENAI_MODEL
