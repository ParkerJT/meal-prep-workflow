from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_uid, get_firestore, require_subscription
from app.services.agents.errors import WorkflowRejection
from app.services.agents.models import GenerateResponse, UserRequest
from app.services.agents.workflow import run_workflow
from app.services.firestore import generation_preferences as prefs_svc

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.post("/generate", response_model=GenerateResponse)
def generate_workflow(
    body: UserRequest,
    _subscription: dict = Depends(require_subscription),
    uid: str = Depends(get_current_uid),
    db=Depends(get_firestore),
) -> GenerateResponse:
    global_instructions = prefs_svc.get_generation_preferences(db, uid)
    try:
        return run_workflow(
            body,
            global_instructions=global_instructions or None,
        )
    except WorkflowRejection as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
