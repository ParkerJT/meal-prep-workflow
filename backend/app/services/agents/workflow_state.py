from __future__ import annotations

from typing import Literal, TypedDict

from openai import OpenAI

from app.services.agents.models import ConvertedRecipe, OriginalRecipe, UserRequest

SourceType = Literal["web", "youtube", "text"]
ExtractionRoute = Literal["youtube", "web", "text"]


class WorkflowState(TypedDict, total=False):
    user_request: UserRequest
    openai_client: OpenAI
    global_instructions: str | None
    source_url: str | None
    source_type: SourceType | None
    extraction_route: ExtractionRoute | None
    raw_content: str | None
    youtube_meta: dict | None
    original_recipe: OriginalRecipe | None
    converted_recipe: ConvertedRecipe | None
    rejection: dict[str, str] | None
