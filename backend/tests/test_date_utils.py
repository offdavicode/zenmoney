from datetime import datetime, timedelta

from utils.date_utils import utc_to_brasilia


def test_utc_timestamp_is_converted_to_previous_brasilia_day_when_needed():
    utc_timestamp = datetime(2026, 6, 11, 2, 30)

    brasilia_timestamp = utc_to_brasilia(utc_timestamp)

    assert brasilia_timestamp.isoformat() == "2026-06-10T23:30:00-03:00"
    assert brasilia_timestamp.utcoffset() == -timedelta(hours=3)
