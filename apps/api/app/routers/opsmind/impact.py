from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/impact", tags=["impact"])


@router.get("/summary")
def impact_summary(current_user: CurrentUser = Depends(require("opsmind.impact.read"))):
    return {"impact": "No widespread impact detected."}
