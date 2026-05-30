from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_subscription
from app.services.agents.errors import WorkflowRejection
from app.services.agents.models import GenerateResponse, UserRequest
from app.services.agents.workflow import run_workflow

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.post("/generate", response_model=GenerateResponse)
def generate_workflow(
    body: UserRequest,
    _subscription: dict = Depends(require_subscription),
) -> GenerateResponse:
    try:
        return run_workflow(body)
    except WorkflowRejection as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
