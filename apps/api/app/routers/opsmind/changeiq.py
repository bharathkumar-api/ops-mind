from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/changeiq", tags=["changeiq"])


@router.get("/records")
def list_changes(current_user: CurrentUser = Depends(require("opsmind.changeiq.read"))):
    return [{"id": "chg-001", "summary": "Deploy payments-api 2024.10.12"}]
