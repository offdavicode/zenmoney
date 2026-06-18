from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.report import (
    CategoryReportItem,
    EmotionReportItem,
    SpendingTriggerReportItem,
    SummaryReport,
    VisualReportResponse,
)
from schemas.emotion_analysis import EmotionSpendingAnalysisResponse
from schemas.prediction import BalancePredictionResponse
from schemas.survival import SurvivalModeResponse
from services.report_service import ReportService, ReportServiceError
from services.emotion_analysis_service import EmotionAnalysisService
from services.prediction_service import PredictionService
from services.budget_service import BudgetServiceError
from services.survival_service import SurvivalService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/balance-prediction", response_model=BalancePredictionResponse)
def get_balance_prediction(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PredictionService(db).predict_month_end_balance(
        current_user, start_date, end_date
    )


@router.get("/summary", response_model=SummaryReport)
def get_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    try:
        return service.get_summary(current_user, month, start_date, end_date)
    except ReportServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/by-emotion", response_model=list[EmotionReportItem])
def get_by_emotion(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    try:
        return service.get_by_emotion(
            current_user, month, start_date, end_date, category_id
        )
    except ReportServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/by-category", response_model=list[CategoryReportItem])
def get_by_category(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    try:
        return service.get_by_category(
            current_user, month, start_date, end_date, category_id
        )
    except ReportServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/visual", response_model=VisualReportResponse)
def get_visual_report(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    try:
        return service.get_visual_report(
            current_user, month, start_date, end_date, category_id
        )
    except ReportServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/survival-mode", response_model=SurvivalModeResponse)
def get_survival_mode(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return SurvivalService(db).evaluate_mode(current_user, month)
    except BudgetServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/triggers", response_model=list[SpendingTriggerReportItem])
def get_spending_triggers(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    try:
        return service.get_spending_triggers(
            current_user, month, start_date, end_date, category_id
        )
    except ReportServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/emotion-spending-analysis", response_model=EmotionSpendingAnalysisResponse)
def get_emotion_spending_analysis(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return EmotionAnalysisService(db).get_analysis(
            current_user,
            month,
            start_date,
            end_date,
            category_id,
        )
    except ReportServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
