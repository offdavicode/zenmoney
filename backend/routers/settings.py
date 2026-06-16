from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.budget import BudgetAlertCheckResponse, BudgetSettingsResponse, BudgetSettingsUpdate
from schemas.survival import SurvivalSettingResponse, SurvivalSettingUpdate
from schemas.user import (
    AccountDeleteRequest,
    AccountDeleteResponse,
    PasswordChangeResponse,
    UserPasswordUpdate,
    UserProfileUpdate,
    UserResponse,
)
from services.account_service import AccountService, AccountServiceError
from services.alert_service import AlertService
from services.auth_service import AuthService, AuthServiceError
from services.budget_service import BudgetService, BudgetServiceError
from services.survival_service import SurvivalService

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


@router.get("/survival-mode", response_model=SurvivalSettingResponse)
def get_survival_setting(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SurvivalService(db).get_setting(current_user)


@router.put("/survival-mode", response_model=SurvivalSettingResponse)
def update_survival_setting(
    payload: SurvivalSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SurvivalService(db).update_setting(current_user, payload)


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


@router.delete("/account", response_model=AccountDeleteResponse)
def delete_account(
    payload: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return AccountService(db).delete_account(current_user, payload)
    except AccountServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
