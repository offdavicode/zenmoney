from datetime import date, datetime, timedelta, timezone


BRASILIA_TZ = timezone(timedelta(hours=-3))


def current_month_label() -> str:
    today = datetime.now(BRASILIA_TZ).date()
    return f"{today.year:04d}-{today.month:02d}"


def parse_month_label(month: str | None) -> tuple[str, date, date]:
    label = month or current_month_label()
    try:
        year_text, month_text = label.split("-", 1)
        year = int(year_text)
        month_number = int(month_text)
        start = date(year, month_number, 1)
    except ValueError as exc:
        raise ValueError("O mês deve usar o formato AAAA-MM.") from exc

    if month_number == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month_number + 1, 1)

    return label, start, end
