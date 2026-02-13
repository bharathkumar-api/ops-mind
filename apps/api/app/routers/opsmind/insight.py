from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/insight", tags=["insight"])


@router.get("/highlights")
def insight_highlights(current_user: CurrentUser = Depends(require("opsmind.insight.read"))):
    return {"highlights": ["RCA automation improved MTTR by 18%"]}
