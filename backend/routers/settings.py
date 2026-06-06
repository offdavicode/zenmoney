from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.budget import BudgetAlertCheckResponse, BudgetSettingsResponse, BudgetSettingsUpdate
from schemas.user import PasswordChangeResponse, UserPasswordUpdate, UserProfileUpdate, UserResponse
from services.alert_service import AlertService
from services.auth_service import AuthService, AuthServiceError
from services.budget_service import BudgetService, BudgetServiceError

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/budget", response_model=BudgetSettingsResponse)
def get_budget(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = BudgetService(db)
    try:
        return service.get_budget_settings(current_user, month)
    except BudgetServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/budget", response_model=BudgetSettingsResponse)
def update_budget(
    payload: BudgetSettingsUpdate,
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = BudgetService(db)
    try:
        return service.update_budget_settings(current_user, payload, month)
    except BudgetServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/budget/alert", response_model=BudgetAlertCheckResponse)
def check_budget_alert(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AlertService(db)
    try:
        return service.check_budget_alert(current_user, month)
    except BudgetServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.update_profile(current_user, payload)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/password", response_model=PasswordChangeResponse)
def update_password(
    payload: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.change_password(current_user, payload)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
