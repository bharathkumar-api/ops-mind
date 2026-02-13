from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/risk", tags=["risk"])


@router.post("/run")
def run_risk(current_user: CurrentUser = Depends(require("opsmind.risk.run"))):
    return {"risk": "moderate"}
