from datetime import datetime
from zoneinfo import ZoneInfo


BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


def now_in_brasilia() -> datetime:
    return datetime.now(BRASILIA_TZ)


def to_brasilia(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BRASILIA_TZ)
    return dt.astimezone(BRASILIA_TZ)


def format_date_br(dt: datetime) -> str:
    return to_brasilia(dt).strftime("%d/%m/%Y")

