from datetime import datetime

from pydantic import BaseModel, model_validator

from app.services.agents.models import ConvertedRecipe, OriginalRecipeDocument


class SavedRecipeResponse(BaseModel):
    id: str
    recipe_id: str
    saved_at: datetime
    notes: str
    converted_recipe: ConvertedRecipe | None
    published: bool
    copied_from_user_id: str | None
    copied_from_saved_recipe_id: str | None


class SavedRecipeCreate(BaseModel):
    recipe_id: str | None = None
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None
    published: bool = False
    source_owner_user_id: str | None = None
    source_saved_recipe_id: str | None = None

    @model_validator(mode="after")
    def copy_requires_both_sources(self):
        a, b = self.source_owner_user_id, self.source_saved_recipe_id
        if (a is None) != (b is None):
            raise ValueError(
                "source_owner_user_id and source_saved_recipe_id must both be set for copy-from-published"
            )
        return self

    @model_validator(mode="after")
    def recipe_id_or_copy(self):
        if self.source_owner_user_id and self.source_saved_recipe_id:
            return self
        if not self.recipe_id:
            raise ValueError("recipe_id is required when not copying from a published recipe")
        return self


class SavedRecipeUpdate(BaseModel):
    notes: str | None = None
    converted_recipe: ConvertedRecipe | None = None
    published: bool | None = None
    recipe_id: str | None = None


class PublishedRecipeSummary(BaseModel):
    owner_user_id: str
    saved_recipe_id: str
    saved_at: datetime
    converted_recipe: ConvertedRecipe | None


class PublishedRecipeDetail(BaseModel):
    owner_user_id: str
    saved_recipe_id: str
    saved_at: datetime
    converted_recipe: ConvertedRecipe | None
    recipe_id: str


class PaginatedPublishedResponse(BaseModel):
    items: list[PublishedRecipeSummary]
    next_cursor: str | None = None
