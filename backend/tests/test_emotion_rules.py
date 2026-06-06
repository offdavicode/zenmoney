from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, align_stored_emotions
from models import Transaction, User
from utils.emotion_rules import DEFAULT_EMOTION, VALID_EMOTIONS, build_emotion_options, normalize_emotion

REQUIRED_RF04_EMOTIONS = {
    "calma",
    "felicidade",
    "raiva",
    "frustracao",
    "empolgacao",
    "ansiedade",
    "estresse",
    "indiferenca",
    "satisfacao",
    "tedio",
}


def test_normalize_emotion_defaults_blank_values() -> None:
    assert normalize_emotion(None) == DEFAULT_EMOTION
    assert normalize_emotion("") == DEFAULT_EMOTION
    assert normalize_emotion("   ") == DEFAULT_EMOTION


def test_normalize_emotion_accepts_known_values_case_insensitively() -> None:
    assert normalize_emotion(" ANSIEDADE ") == "ansiedade"
    assert normalize_emotion("Felicidade") == "felicidade"


def test_normalize_emotion_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        normalize_emotion("desconhecida")


def test_emotion_options_cover_valid_emotions() -> None:
    options = build_emotion_options()

    assert {option["value"] for option in options} == set(VALID_EMOTIONS)
    assert all(option["label"] for option in options)


def test_valid_emotions_match_rf04_list() -> None:
    assert set(VALID_EMOTIONS) == REQUIRED_RF04_EMOTIONS | {DEFAULT_EMOTION}


def test_stored_emotion_alignment_preserves_only_valid_expense_emotions() -> None:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        user = User(
            name="Usuario Migracao",
            email="migracao@example.com",
            password_hash="hash",
        )
        db.add(user)
        db.flush()
        valid_expense = Transaction(
            user_id=user.id,
            type="expense",
            amount=Decimal("10.00"),
            date=date(2026, 6, 6),
            emotion="calma",
        )
        legacy_expense = Transaction(
            user_id=user.id,
            type="expense",
            amount=Decimal("20.00"),
            date=date(2026, 6, 6),
            emotion="culpa",
        )
        emotional_income = Transaction(
            user_id=user.id,
            type="income",
            amount=Decimal("30.00"),
            date=date(2026, 6, 6),
            emotion="felicidade",
        )
        db.add_all([valid_expense, legacy_expense, emotional_income])
        db.commit()

        align_stored_emotions(db)
        db.refresh(valid_expense)
        db.refresh(legacy_expense)
        db.refresh(emotional_income)

        assert valid_expense.emotion == "calma"
        assert legacy_expense.emotion == DEFAULT_EMOTION
        assert emotional_income.emotion == DEFAULT_EMOTION
