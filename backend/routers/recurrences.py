from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.recurrence import (
    RecurrenceCreate,
    RecurrenceResponse,
    RecurrenceRunDueRequest,
    RecurrenceRunDueResponse,
    RecurrenceUpdate,
)
from services.recurrence_service import RecurrenceService, RecurrenceServiceError

router = APIRouter(prefix="/recurrences", tags=["recurrences"])


def _raise_http_error(exc: RecurrenceServiceError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/", response_model=RecurrenceResponse, status_code=status.HTTP_201_CREATED)
def create_recurrence(
    payload: RecurrenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return RecurrenceService(db).create_recurrence(current_user, payload)
    except RecurrenceServiceError as exc:
        _raise_http_error(exc)


@router.get("/", response_model=list[RecurrenceResponse])
def list_recurrences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RecurrenceService(db).list_recurrences(current_user)


@router.post("/run-due", response_model=RecurrenceRunDueResponse)
def run_due_recurrences(
    payload: RecurrenceRunDueRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    through_date = payload.through_date if payload else None
    return RecurrenceService(db).run_due(current_user, through_date)


@router.get("/{recurrence_id}", response_model=RecurrenceResponse)
def get_recurrence(
    recurrence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return RecurrenceService(db).get_recurrence(current_user, recurrence_id)
    except RecurrenceServiceError as exc:
        _raise_http_error(exc)


@router.put("/{recurrence_id}", response_model=RecurrenceResponse)
def update_recurrence(
    recurrence_id: int,
    payload: RecurrenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return RecurrenceService(db).update_recurrence(current_user, recurrence_id, payload)
    except RecurrenceServiceError as exc:
        _raise_http_error(exc)


@router.patch("/{recurrence_id}/pause", response_model=RecurrenceResponse)
def pause_recurrence(
    recurrence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return RecurrenceService(db).pause_recurrence(current_user, recurrence_id)
    except RecurrenceServiceError as exc:
        _raise_http_error(exc)


@router.patch("/{recurrence_id}/resume", response_model=RecurrenceResponse)
def resume_recurrence(
    recurrence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return RecurrenceService(db).resume_recurrence(current_user, recurrence_id)
    except RecurrenceServiceError as exc:
        _raise_http_error(exc)


@router.delete("/{recurrence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurrence(
    recurrence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        RecurrenceService(db).delete_recurrence(current_user, recurrence_id)
        return None
    except RecurrenceServiceError as exc:
        _raise_http_error(exc)
