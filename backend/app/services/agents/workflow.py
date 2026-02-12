from app.services.agents.models import UserRequest, OriginalRecipe, ConvertedRecipe, ConversionRequest
from app.services.agents.extraction import recipe_extraction_workflow
import asyncio
from app.config import Settings

settings = Settings()

def run_workflow(user_request: UserRequest) -> OriginalRecipe:

    original_recipe = recipe_extraction_workflow(UserRequest.recipe_url)

    return original_recipe
