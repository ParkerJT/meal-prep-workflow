from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

# User adjustments packaged
class UserAdjustments(BaseModel):
    target_servings: int # (desired number of servings)
    target_calories: int # (desired calories per serving)
    target_protein: int # (desired protein per serving)

# Initial user input model (coming from frontend)
class UserRequest(BaseModel):
    user_adjustments: UserAdjustments
    input_mode: Literal["url", "text"] = "url"
    recipe_url: str | None = None
    recipe_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _default_input_mode_from_legacy_payload(cls, data):
        if isinstance(data, dict) and "input_mode" not in data and data.get("recipe_url"):
            data = dict(data)
            data.setdefault("input_mode", "url")
        return data

    @model_validator(mode="after")
    def _validate_input_fields(self):
        if self.input_mode == "url":
            if not self.recipe_url or not self.recipe_url.strip():
                raise ValueError("recipe_url is required when input_mode is url")
            if self.recipe_text:
                raise ValueError("recipe_text must not be set when input_mode is url")
        elif self.input_mode == "text":
            if not self.recipe_text or not self.recipe_text.strip():
                raise ValueError("recipe_text is required when input_mode is text")
            if self.recipe_url:
                raise ValueError("recipe_url must not be set when input_mode is text")
        return self

# Ingredient model inside original and converted recipes
class Ingredient(BaseModel):
    name: str # Ingredient name
    quantity: float | int | str # Ingredient quantity
    unit: str | None = None # Ingredient unit (optional)

# Original recipe model (output from extraction agent)
class OriginalRecipe(BaseModel):
    title: str # Recipe name
    description: str | None = None  # Recipe description (optional)
    servings: int # Original number of servings
    ingredients: list[Ingredient]
    instructions: list[str] # List of instructions

# Nutritional information model (for converted recipe)
class NutritionalInfo(BaseModel):
    calories: int # Calories per serving
    protein: int # Protein per serving

# Conversion metadata model (for converted recipe)
class ConversionMetadata(BaseModel):
    original_recipe_url: str # Original recipe URL or empty for pasted text
    conversion_notes: str # Notes on what was converted and why

# Converted recipe model (output from conversion agent)
class ConvertedRecipe(BaseModel):
    title: str # Recipe name
    description: str | None = None  # Recipe description (optional)
    servings: int # Converted number of servings
    ingredients: list[Ingredient]
    instructions: list[str] # List of instructions
    nutritional_info: NutritionalInfo # Nutritional information
    conversion_metadata: ConversionMetadata


class GenerateResponse(BaseModel):
    original_recipe: OriginalRecipe
    converted_recipe: ConvertedRecipe
    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"]


# Firestore document shape for users/{userId}/saved_recipes/{savedRecipeId}
class SavedRecipe(BaseModel):
    saved_at: datetime
    notes: str = ""
    source_url: str | None = None
    source_type: Literal["web", "youtube", "text"] | None = None
    original_recipe: OriginalRecipe | None = None
    converted_recipe: ConvertedRecipe | None = None

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_saved_recipe(cls, data):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "original_recipe_id" in data and "original_recipe" not in data:
            data.pop("original_recipe_id", None)
            data.pop("recipe_id", None)
        return data
