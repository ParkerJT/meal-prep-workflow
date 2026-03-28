from fastapi import APIRouter

from app.services.agents.models import UserRequest, UserAdjustments
from app.services.agents.workflow import run_workflow

router = APIRouter(prefix="/api/test", tags=["test"])


@router.post("/workflow")
async def test_workflow(recipe_url: str, target_servings: int, target_calories: int, target_protein: int):
    """
    Thin alias for manual QA: same pipeline as POST /api/workflow/generate (returns ConvertedRecipe).
    """

    user_request = UserRequest(
        recipe_url=recipe_url,
        user_adjustments=UserAdjustments(
            target_servings=target_servings,
            target_calories=target_calories,
            target_protein=target_protein,
        ),
    )

    try:
        result = run_workflow(user_request)
        return {
            "status": "success",
            "result": result,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
