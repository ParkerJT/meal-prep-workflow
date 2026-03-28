from openai import OpenAI

from app.config import Settings
from app.services.agents.conversion import convert_recipe
from app.services.agents.extraction import recipe_extraction_workflow
from app.services.agents.models import ConvertedRecipe, UserRequest
from app.services.firestore.client import get_firestore_client
from app.services.save_flow import ensure_canonical_original_recipe

settings = Settings()


def run_workflow(user_request: UserRequest) -> ConvertedRecipe:
    db = get_firestore_client()
    original_recipe = recipe_extraction_workflow(db, user_request.recipe_url)
    ensure_canonical_original_recipe(
        db,
        source_url=user_request.recipe_url,
        original_recipe=original_recipe,
        created_by=None,
    )
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return convert_recipe(original_recipe, user_request, client)
