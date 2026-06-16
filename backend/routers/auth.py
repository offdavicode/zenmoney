from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth_dependencies import get_current_token, get_current_user
from database import get_db
from models.user import User
from schemas.user import AccessTokenResponse, LogoutResponse, UserCreate, UserLogin, UserResponse
from services.auth_service import AuthService, AuthServiceError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.register_user(payload)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/login", response_model=AccessTokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.login_user(payload)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/logout", response_model=LogoutResponse)
def logout_user(token: str = Depends(get_current_token), db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.logout_user(token)
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    return current_user
