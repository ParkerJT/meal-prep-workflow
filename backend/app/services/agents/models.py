from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# User adjustments packaged
class UserAdjustments(BaseModel):
    target_servings: int # (desired number of servings)
    target_calories: int # (desired calories per serving)
    target_protein: int # (desired protein per serving)

# Initial user input model (coming from frontend)
class UserRequest(BaseModel):
    recipe_url: str # (web page or YouTube video)
    user_adjustments: UserAdjustments 

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


# Firestore document for original_recipes/{recipeId} — same recipe body as OriginalRecipe,
# plus app-populated metadata (not produced by the LLM). Use when reading/writing Firestore;
# map Firestore Timestamps to/from datetime in the repository layer.
class OriginalRecipeDocument(OriginalRecipe):
    id: str  # document id; equals hash of normalized source_url (see BUILD_PLAN)
    source_url: str
    source_type: Literal["web", "youtube"]
    created_at: datetime
    created_by: str | None = None


# Conversion request model (input to conversion agent)
class ConversionRequest(BaseModel):
    original_recipe: OriginalRecipe
    user_adjustments: UserAdjustments

# Nutritional information model (for converted recipe)
class NutritionalInfo(BaseModel):
    calories: int # Calories per serving
    protein: int # Protein per serving

# Conversion metadata model (for converted recipe)
class ConversionMetadata(BaseModel):
    original_recipe_url: str # Original recipe URL
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


# Firestore document shape for users/{userId}/saved_recipes/{savedRecipeId}
class SavedRecipe(BaseModel):
    recipe_id: str  # original_recipes doc id
    saved_at: datetime
    notes: str = ""
    converted_recipe: ConvertedRecipe | None = None
    published: bool = False
    copied_from_user_id: str | None = None
    copied_from_saved_recipe_id: str | None = None


def original_recipe_from_document(doc: OriginalRecipeDocument) -> OriginalRecipe:
    """Recipe fields only — for Firestore cache hits before LLM extraction."""
    return OriginalRecipe(
        title=doc.title,
        description=doc.description,
        servings=doc.servings,
        ingredients=doc.ingredients,
        instructions=doc.instructions,
    )
