from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from services.transaction_service import TransactionService, TransactionServiceError

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        return service.create_transaction(current_user, payload)
    except TransactionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/", response_model=list[TransactionResponse])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        return service.list_transactions(current_user)
    except TransactionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        return service.get_transaction(current_user, transaction_id)
    except TransactionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        return service.update_transaction(current_user, transaction_id, payload)
    except TransactionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = TransactionService(db)
    try:
        service.delete_transaction(current_user, transaction_id)
        return None
    except TransactionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
