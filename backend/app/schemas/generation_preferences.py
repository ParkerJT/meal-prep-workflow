from pydantic import BaseModel, field_validator

from app.services.user_text import GLOBAL_INSTRUCTIONS_MAX_CHARS, sanitize_user_text


class GenerationPreferencesResponse(BaseModel):
    global_instructions: str = ""


class GenerationPreferencesUpdate(BaseModel):
    global_instructions: str = ""

    @field_validator("global_instructions", mode="before")
    @classmethod
    def _sanitize_global_instructions(cls, value):
        if value is None:
            return ""
        return sanitize_user_text(
            value,
            max_chars=GLOBAL_INSTRUCTIONS_MAX_CHARS,
            field_name="global_instructions",
            required=False,
        )
