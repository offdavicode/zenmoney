from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.report import (
    CategoryReportItem,
    EmotionReportItem,
    SpendingTriggerReportItem,
    SummaryReport,
)
from services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=SummaryReport)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.get_summary(current_user)


@router.get("/by-emotion", response_model=list[EmotionReportItem])
def get_by_emotion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.get_by_emotion(current_user)


@router.get("/by-category", response_model=list[CategoryReportItem])
def get_by_category(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.get_by_category(current_user)


@router.get("/triggers", response_model=list[SpendingTriggerReportItem])
def get_spending_triggers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    return service.get_spending_triggers(current_user)
