from fastapi import APIRouter, Depends

from schemas.dependencies import get_dashboard_controller
from schemas.response import R


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/overview")
def get_dashboard_overview(ctrl=Depends(get_dashboard_controller)):
    return R.success(data=ctrl.get_overview())
