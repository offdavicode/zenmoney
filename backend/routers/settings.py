from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.user import UserResponse
from services.alert_service import AlertService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/budget")
def get_budget(user_id: int = Query(...), db: Session = Depends(get_db)):
    service = AlertService(db)
    try:
        return service.get_budget_status(user_id)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc


@router.put("/budget")
def update_budget(user_id: int = Query(...), db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Budget update has not been implemented yet.",
    )


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile")
def update_profile(user_id: int = Query(...), db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Profile update has not been implemented yet.",
    )
