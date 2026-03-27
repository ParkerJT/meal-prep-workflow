from app.services.agents.models import UserRequest, OriginalRecipe
from app.services.agents.extraction import recipe_extraction_workflow
from app.services.firestore.client import get_firestore_client
from app.config import Settings

settings = Settings()

def run_workflow(user_request: UserRequest) -> OriginalRecipe:
    # Phase 2.5: wire conversion + save_flow.save_from_workflow / POST .../from-workflow after extract.
    db = get_firestore_client()
    original_recipe = recipe_extraction_workflow(db, user_request.recipe_url)

    return original_recipe
