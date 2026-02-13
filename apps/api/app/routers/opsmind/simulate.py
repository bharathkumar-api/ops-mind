from fastapi import APIRouter, Depends
from app.core.security import CurrentUser, require

router = APIRouter(prefix="/opsmind/simulate", tags=["simulate"])


@router.post("/run")
def run_simulation(current_user: CurrentUser = Depends(require("opsmind.simulate.run"))):
    return {"status": "simulation_complete"}
