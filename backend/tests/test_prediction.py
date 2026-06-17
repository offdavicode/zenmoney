from datetime import date
from decimal import Decimal

from utils.date_utils import now_in_brasilia


CENTS = Decimal("0.01")


def _register_and_login(client, name: str, email: str) -> dict[str, str]:
    password = "Senha@123"
    client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _money(value: Decimal) -> str:
    return str(value.quantize(CENTS))


def _next_month_start(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


def _previous_month_start(month_start: date) -> date:
    if month_start.month == 1:
        return date(month_start.year - 1, 12, 1)
    return date(month_start.year, month_start.month - 1, 1)


def _days_remaining(today: date) -> int:
    return max((_next_month_start(today.replace(day=1)) - today).days - 1, 0)


def _create_transaction(
    client,
    headers: dict[str, str],
    transaction_type: str,
    amount: str,
    transaction_date: date,
):
    emotion = "felicidade" if transaction_type == "income" else "calma"
    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": transaction_type,
            "amount": amount,
            "date": transaction_date.isoformat(),
            "emotion": emotion,
        },
    )
    assert response.status_code == 201
    return response


def _create_recurrence(
    client,
    headers: dict[str, str],
    recurrence_type: str,
    amount: str,
    start_date: date,
    end_date: date | None = None,
):
    emotion = "felicidade" if recurrence_type == "income" else "calma"
    response = client.post(
        "/api/recurrences/",
        headers=headers,
        json={
            "type": recurrence_type,
            "amount": amount,
            "emotion": emotion,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date is not None else None,
            "day_of_month": start_date.day,
        },
    )
    assert response.status_code == 201
    return response


def test_balance_prediction_requires_authentication(client):
    response = client.get("/api/reports/balance-prediction")

    assert response.status_code == 401


def test_prediction_without_data_returns_zeroes_and_insufficient_confidence(client):
    headers = _register_and_login(client, "Previsao Vazia", "prediction-empty@example.com")
    today = now_in_brasilia().date()

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["month"] == f"{today.year:04d}-{today.month:02d}"
    assert data["calculated_on"] == today.isoformat()
    assert data["days_remaining"] == _days_remaining(today)
    assert data["current_income"] == "0.00"
    assert data["current_expense"] == "0.00"
    assert data["current_month_balance"] == "0.00"
    assert data["expected_future_recurring_income"] == "0.00"
    assert data["expected_future_recurring_expense"] == "0.00"
    assert data["historical_daily_variable_expense_average"] == "0.00"
    assert data["expected_remaining_variable_expense"] == "0.00"
    assert data["predicted_end_balance"] == "0.00"
    assert data["history_months_used"] == []
    assert data["confidence_level"] == "insufficient"


def test_prediction_uses_current_month_daily_expense_average(client):
    headers = _register_and_login(client, "Previsao Mensal", "prediction-month@example.com")
    today = now_in_brasilia().date()
    _create_transaction(client, headers, "income", "1000.00", today)
    _create_transaction(client, headers, "expense", "100.00", today)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    daily_average = Decimal("100.00") / Decimal(today.day)
    expected_remaining = daily_average * Decimal(_days_remaining(today))
    predicted_end_balance = Decimal("900.00") - expected_remaining

    assert data["current_income"] == "1000.00"
    assert data["current_expense"] == "100.00"
    assert data["current_month_balance"] == "900.00"
    assert data["historical_daily_variable_expense_average"] == _money(daily_average)
    assert data["expected_remaining_variable_expense"] == _money(expected_remaining)
    assert data["predicted_end_balance"] == _money(predicted_end_balance)
    assert data["history_months_used"] == []
    assert data["confidence_level"] != "insufficient"


def test_prediction_ignores_previous_month_when_calculating_current_forecast(client):
    headers = _register_and_login(client, "Previsao Atual", "prediction-current@example.com")
    today = now_in_brasilia().date()
    previous_month = _previous_month_start(today.replace(day=1))
    _create_transaction(client, headers, "expense", "999.00", previous_month)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["current_expense"] == "0.00"
    assert data["historical_daily_variable_expense_average"] == "0.00"
    assert data["expected_remaining_variable_expense"] == "0.00"
    assert data["predicted_end_balance"] == "0.00"
    assert data["history_months_used"] == []


def test_recurrences_are_not_projected_until_generated_as_current_transactions(client):
    headers = _register_and_login(client, "Recorrencia Atual", "prediction-recurrence@example.com")
    today = now_in_brasilia().date()
    _create_recurrence(client, headers, "expense", "120.00", today)

    before_generation = client.get("/api/reports/balance-prediction", headers=headers).json()
    run_response = client.post("/api/recurrences/run-due", headers=headers)
    after_generation = client.get("/api/reports/balance-prediction", headers=headers).json()

    assert run_response.json()["generated_count"] == 1
    assert before_generation["current_expense"] == "0.00"
    assert before_generation["expected_future_recurring_expense"] == "0.00"
    assert before_generation["predicted_end_balance"] == "0.00"
    assert after_generation["current_expense"] == "120.00"
    assert after_generation["expected_future_recurring_expense"] == "0.00"

    daily_average = Decimal("120.00") / Decimal(today.day)
    expected_remaining = daily_average * Decimal(_days_remaining(today))
    assert after_generation["predicted_end_balance"] == _money(
        Decimal("-120.00") - expected_remaining
    )


def test_prediction_is_isolated_by_user_and_updates_dynamically(client):
    first_headers = _register_and_login(client, "Primeira Previsao", "prediction-first@example.com")
    second_headers = _register_and_login(client, "Segunda Previsao", "prediction-second@example.com")
    today = now_in_brasilia().date()
    _create_transaction(client, second_headers, "expense", "900.00", today)

    before = client.get("/api/reports/balance-prediction", headers=first_headers).json()
    _create_transaction(client, first_headers, "expense", "50.00", today)
    after = client.get("/api/reports/balance-prediction", headers=first_headers).json()

    daily_average = Decimal("50.00") / Decimal(today.day)
    expected_remaining = daily_average * Decimal(_days_remaining(today))

    assert before["current_expense"] == "0.00"
    assert after["current_expense"] == "50.00"
    assert after["predicted_end_balance"] == _money(
        Decimal("-50.00") - expected_remaining
    )
