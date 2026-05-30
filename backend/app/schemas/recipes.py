from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from app.services.agents.models import ConvertedRecipe, OriginalRecipe


class SavedRecipeResponse(BaseModel):
    id: str
    saved_at: datetime
    notes: str
    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"] | None = None
    original_recipe: OriginalRecipe | None = None
    converted_recipe: ConvertedRecipe | None = None


class SavedRecipeCreate(BaseModel):
    notes: str = ""
    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"] | None = None
    original_recipe: OriginalRecipe | None = None
    converted_recipe: ConvertedRecipe | None = None


class SavedRecipeUpdate(BaseModel):
    notes: str | None = None
    converted_recipe: ConvertedRecipe | None = None
    original_recipe: OriginalRecipe | None = None
    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"] | None = None


class WorkflowSaveCreate(BaseModel):
    """Create a user save after extraction with embedded recipe snapshots."""

    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"]
    original_recipe: OriginalRecipe
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None


class GeneratedSaveCreate(BaseModel):
    """Create a saved recipe after /workflow/generate using the generate response payload."""

    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"]
    original_recipe: OriginalRecipe
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None

    @model_validator(mode="after")
    def _require_converted_recipe(self):
        if self.converted_recipe is None:
            raise ValueError("converted_recipe is required")
        return self
