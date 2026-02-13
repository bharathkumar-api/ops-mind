from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/correlate", tags=["correlate"])


@router.post("/run")
def run_correlation(current_user: CurrentUser = Depends(require("opsmind.correlate.run"))):
    return {"status": "correlation_started"}
