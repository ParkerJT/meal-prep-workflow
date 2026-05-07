from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from app.services.agents.models import ConvertedRecipe, OriginalRecipe, OriginalRecipeDocument


class SavedRecipeResponse(BaseModel):
    id: str
    original_recipe_id: str
    saved_at: datetime
    notes: str
    converted_recipe: ConvertedRecipe | None


class SavedRecipeCreate(BaseModel):
    original_recipe_id: str | None = None
    recipe_id: str | None = None
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None

    @model_validator(mode="after")
    def _ensure_original_recipe_id(self):
        if self.original_recipe_id is None and self.recipe_id is None:
            raise ValueError("original_recipe_id is required")
        if self.original_recipe_id is None:
            self.original_recipe_id = self.recipe_id
        return self


class SavedRecipeUpdate(BaseModel):
    notes: str | None = None
    converted_recipe: ConvertedRecipe | None = None
    original_recipe_id: str | None = None
    recipe_id: str | None = None

    @model_validator(mode="after")
    def _sync_aliases(self):
        if self.original_recipe_id is None and self.recipe_id is not None:
            self.original_recipe_id = self.recipe_id
        return self


class WorkflowSaveCreate(BaseModel):
    """Create a user save after extraction: ensures ``original_recipes`` then ``saved_recipes`` (§2.4)."""

    source_url: str
    source_type: Literal["web", "youtube"]
    original_recipe: OriginalRecipe
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None


class GeneratedSaveCreate(BaseModel):
    """Create a saved recipe after /workflow/generate using canonical recipe id from source_url."""

    source_url: str
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None
