from pydantic import BaseModel
from datetime import datetime

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


class DatabaseRecord(BaseModel):
    id: str # Unique recipe ID
    created_at: datetime # Timestamp of creation
    recipe: ConvertedRecipe
