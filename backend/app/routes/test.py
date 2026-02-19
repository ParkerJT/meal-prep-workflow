from fastapi import APIRouter
from app.services.agents.models import UserRequest, UserAdjustments
from app.services.agents.workflow import run_workflow
from app.services.agents.extraction import scrape_web_page

router = APIRouter(prefix="/api/test", tags=["test"])

@router.post("/workflow")
async def test_workflow(recipe_url: str, target_servings: int, target_calories: int, target_protein: int):
    """
    Test endpoint for the run_workflow function.
    Accepts a UserRequest and returns the extracted OriginalRecipe.
    """

    user_request = UserRequest(
        recipe_url=recipe_url,
        user_adjustments=UserAdjustments(
            target_servings=target_servings,
            target_calories=target_calories,
            target_protein=target_protein
        )
    )

    try:
        original_recipe = run_workflow(user_request)
        return {
            "status": "success",
            "result": original_recipe
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }