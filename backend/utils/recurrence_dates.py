from calendar import monthrange
from datetime import date


def scheduled_date(year: int, month: int, day_of_month: int) -> date:
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day_of_month, last_day))


def first_scheduled_on_or_after(reference_date: date, day_of_month: int) -> date:
    candidate = scheduled_date(reference_date.year, reference_date.month, day_of_month)
    if candidate >= reference_date:
        return candidate

    if reference_date.month == 12:
        return scheduled_date(reference_date.year + 1, 1, day_of_month)
    return scheduled_date(reference_date.year, reference_date.month + 1, day_of_month)


def next_scheduled_date(current_date: date, day_of_month: int) -> date:
    if current_date.month == 12:
        return scheduled_date(current_date.year + 1, 1, day_of_month)
    return scheduled_date(current_date.year, current_date.month + 1, day_of_month)
