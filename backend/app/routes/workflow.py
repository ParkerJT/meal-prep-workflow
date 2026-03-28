from fastapi import APIRouter

from app.services.agents.models import ConvertedRecipe, UserRequest
from app.services.agents.workflow import run_workflow

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.post("/generate", response_model=ConvertedRecipe)
def generate_workflow(body: UserRequest) -> ConvertedRecipe:
    return run_workflow(body)
