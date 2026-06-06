from collections.abc import Generator

from sqlalchemy import create_engine, event, update
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
    from models import budget_alert, budget_limit, category, recurrence, revoked_token, transaction, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_default_categories(db)
        align_stored_emotions(db)


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
                (model.type != "expense")
                | (model.emotion.not_in(VALID_EMOTIONS))
            )
            .values(emotion=DEFAULT_EMOTION)
        )
    db.commit()
