from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, or_, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine: Engine = create_engine(
    settings.database_url,
    connect_args=_sqlite_connect_args(settings.database_url),
)


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    from models import budget_alert, budget_limit, category, recurrence, revoked_token, survival_setting, transaction, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_transaction_is_recurring_column()
    with SessionLocal() as db:
        seed_default_categories(db)
        align_stored_emotions(db)
        align_stored_recurrence_schedules(db)
        align_stored_recurring_transactions(db)


def seed_default_categories(db: Session) -> None:
    from sqlalchemy import select

    from models.category import Category
    from utils.category_rules import build_default_category_rows

    default_rows = build_default_category_rows()
    for row in default_rows:
        existing_category = db.scalar(
            select(Category).where(
                Category.name == row["name"],
                Category.type == row["type"],
                Category.user_id.is_(None),
            )
        )
        if existing_category is None:
            db.add(Category(**row))

    db.commit()


def align_stored_emotions(db: Session) -> None:
    from models.recurrence import Recurrence
    from models.transaction import Transaction
    from utils.emotion_rules import DEFAULT_EMOTION, VALID_EMOTIONS

    for model in (Transaction, Recurrence):
        db.execute(
            update(model)
            .where(
                model.emotion.not_in(VALID_EMOTIONS)
            )
            .values(emotion=DEFAULT_EMOTION)
        )
    db.commit()


def align_stored_recurrence_schedules(db: Session) -> None:
    from sqlalchemy import select

    from models.recurrence import Recurrence

    invalid_recurrences = db.scalars(
        select(Recurrence).where(
            or_(
                Recurrence.day_of_month.is_(None),
                Recurrence.day_of_month < 1,
                Recurrence.day_of_month > 31,
                Recurrence.frequency != "monthly",
            )
        )
    )
    for recurrence in invalid_recurrences:
        if recurrence.day_of_month is None or not 1 <= recurrence.day_of_month <= 31:
            recurrence.day_of_month = recurrence.start_date.day
        recurrence.frequency = "monthly"

    db.commit()


def ensure_transaction_is_recurring_column() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    transaction_columns = {
        column["name"]
        for column in inspect(engine).get_columns("transactions")
    }
    if "is_recurring" in transaction_columns:
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "ALTER TABLE transactions "
            "ADD COLUMN is_recurring BOOLEAN NOT NULL DEFAULT 0"
        )


def align_stored_recurring_transactions(db: Session) -> None:
    from models.transaction import Transaction

    db.execute(
        update(Transaction)
        .where(Transaction.recurrence_id.is_not(None))
        .values(is_recurring=True)
    )
    db.commit()
