from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def get_summary(user_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    service = ReportService(db)
    try:
        return service.get_summary(user_id)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc


@router.get("/by-emotion")
def get_by_emotion(user_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    service = ReportService(db)
    try:
        return service.get_by_emotion(user_id)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc


@router.get("/by-category")
def get_by_category(user_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    service = ReportService(db)
    try:
        return service.get_by_category(user_id)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc


@router.get("/triggers")
def get_spending_triggers(user_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    service = ReportService(db)
    try:
        return service.get_spending_triggers(user_id)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc

