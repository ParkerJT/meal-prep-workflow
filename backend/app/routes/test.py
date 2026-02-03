from fastapi import APIRouter
from app.services.agents.models import UserRequest, UserAdjustments
from app.services.agents.workflow import run_workflow

router = APIRouter(prefix="/api/test", tags=["test"])

@router.post("/workflow")
async def test_workflow():
    """
    Test endpoint for the run_workflow function.
    Accepts a UserRequest and returns the extracted OriginalRecipe.
    """

    # IGNORE FOR NOW
    user_request = UserRequest(
        recipe_url="https://www.youtube.com/watch?v=CfchYxh7Q9g",
        user_adjustments=UserAdjustments(
            target_servings=1,
            target_calories=100,
            target_protein=10
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

