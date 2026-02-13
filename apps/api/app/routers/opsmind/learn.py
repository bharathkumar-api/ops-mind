from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/learn", tags=["learn"])


@router.post("/feedback")
def submit_feedback(current_user: CurrentUser = Depends(require("opsmind.learn.write"))):
    return {"status": "feedback_recorded"}
