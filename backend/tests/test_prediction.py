from datetime import date

from utils.date_utils import now_in_brasilia


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


def _next_month_start(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


def _previous_month_start(month_start: date) -> date:
    if month_start.month == 1:
        return date(month_start.year - 1, 12, 1)
    return date(month_start.year, month_start.month - 1, 1)


def _create_transaction(
    client,
    headers: dict[str, str],
    transaction_type: str,
    amount: str,
    transaction_date: date,
):
    return client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": transaction_type,
            "amount": amount,
            "date": transaction_date.isoformat(),
        },
    )


def _create_recurrence(
    client,
    headers: dict[str, str],
    recurrence_type: str,
    amount: str,
    start_date: date,
    end_date: date | None = None,
):
    return client.post(
        "/api/recurrences/",
        headers=headers,
        json={
            "type": recurrence_type,
            "amount": amount,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date is not None else None,
            "day_of_month": start_date.day,
        },
    )


def test_balance_prediction_requires_authentication(client):
    response = client.get("/api/reports/balance-prediction")

    assert response.status_code == 401


def test_prediction_without_data_returns_zeroes_and_insufficient_confidence(client):
    headers = _register_and_login(client, "Previsao Vazia", "prediction-empty@example.com")
    today = now_in_brasilia().date()
    next_month = _next_month_start(today.replace(day=1))

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["month"] == f"{today.year:04d}-{today.month:02d}"
    assert data["calculated_on"] == today.isoformat()
    assert data["days_remaining"] == (next_month - today).days - 1
    assert data["current_month_balance"] == "0.00"
    assert data["predicted_end_balance"] == "0.00"
    assert data["history_months_used"] == []
    assert data["confidence_level"] == "insufficient"


def test_prediction_combines_current_balance_and_future_recurrences(client):
    headers = _register_and_login(client, "Previsao Completa", "prediction-full@example.com")
    today = now_in_brasilia().date()
    _create_transaction(client, headers, "income", "1000.00", today)
    _create_transaction(client, headers, "expense", "100.00", today)
    _create_recurrence(client, headers, "income", "2000.00", today)
    _create_recurrence(client, headers, "expense", "500.00", today)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["current_income"] == "1000.00"
    assert data["current_expense"] == "100.00"
    assert data["current_month_balance"] == "900.00"
    assert data["expected_future_recurring_income"] == "2000.00"
    assert data["expected_future_recurring_expense"] == "500.00"
    assert data["predicted_end_balance"] == "2400.00"


def test_generated_recurrence_is_not_counted_twice(client):
    headers = _register_and_login(client, "Sem Duplicacao", "prediction-no-double@example.com")
    today = now_in_brasilia().date()
    _create_recurrence(client, headers, "expense", "120.00", today)
    run_response = client.post("/api/recurrences/run-due", headers=headers)
    assert run_response.json()["generated_count"] == 1

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["current_expense"] == "120.00"
    assert data["expected_future_recurring_expense"] == "0.00"
    assert data["predicted_end_balance"] == "-120.00"


def test_overdue_recurrence_not_yet_generated_is_still_projected(client):
    headers = _register_and_login(client, "Recorrencia Pendente", "prediction-overdue@example.com")
    today = now_in_brasilia().date()
    month_start = today.replace(day=1)
    _create_recurrence(client, headers, "expense", "300.00", month_start)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["current_expense"] == "0.00"
    assert data["expected_future_recurring_expense"] == "300.00"
    assert data["predicted_end_balance"] == "-300.00"


def test_prediction_uses_up_to_three_complete_history_months(client):
    headers = _register_and_login(client, "Historico Completo", "prediction-history@example.com")
    today = now_in_brasilia().date()
    month_end = today.replace(day=1)
    expected_labels = []

    for _ in range(3):
        month_start = _previous_month_start(month_end)
        days_in_month = (month_end - month_start).days
        _create_transaction(
            client,
            headers,
            "expense",
            f"{days_in_month}.00",
            month_start,
        )
        expected_labels.append(f"{month_start.year:04d}-{month_start.month:02d}")
        month_end = month_start

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert [month["month"] for month in data["history_months_used"]] == expected_labels
    assert data["historical_daily_variable_expense_average"] == "1.00"
    assert data["expected_remaining_variable_expense"] == f"{data['days_remaining']}.00"
    assert data["predicted_end_balance"] == f"-{data['days_remaining']}.00"
    assert data["confidence_level"] == "high"


def test_empty_history_months_are_ignored(client):
    headers = _register_and_login(client, "Historico com Lacuna", "prediction-gap@example.com")
    today = now_in_brasilia().date()
    current_month = today.replace(day=1)
    previous_month = _previous_month_start(current_month)
    two_months_ago = _previous_month_start(previous_month)
    three_months_ago = _previous_month_start(two_months_ago)
    _create_transaction(client, headers, "expense", "31.00", previous_month)
    _create_transaction(client, headers, "expense", "31.00", three_months_ago)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert [month["month"] for month in data["history_months_used"]] == [
        f"{previous_month.year:04d}-{previous_month.month:02d}",
        f"{three_months_ago.year:04d}-{three_months_ago.month:02d}",
    ]
    assert data["confidence_level"] == "medium"


def test_historical_recurring_expenses_are_excluded_from_variable_average(client):
    headers = _register_and_login(client, "Historico Variavel", "prediction-variable@example.com")
    today = now_in_brasilia().date()
    current_month = today.replace(day=1)
    previous_month = _previous_month_start(current_month)
    previous_month_days = (current_month - previous_month).days
    _create_transaction(
        client,
        headers,
        "expense",
        f"{previous_month_days}.00",
        previous_month,
    )
    recurrence = _create_recurrence(
        client,
        headers,
        "expense",
        "999.00",
        previous_month,
        previous_month,
    ).json()
    client.post("/api/recurrences/run-due", headers=headers)
    client.delete(f"/api/recurrences/{recurrence['id']}", headers=headers)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["history_months_used"][0]["variable_expense"] == f"{previous_month_days}.00"
    assert data["historical_daily_variable_expense_average"] == "1.00"
    assert data["confidence_level"] == "low"

    transactions = client.get("/api/transactions/", headers=headers).json()
    recurring_transaction = next(
        transaction for transaction in transactions if transaction["amount"] == "999.00"
    )
    assert recurring_transaction["recurrence_id"] is None
    assert recurring_transaction["is_recurring"] is True


def test_paused_recurrences_are_not_projected(client):
    headers = _register_and_login(client, "Previsao Pausada", "prediction-paused@example.com")
    today = now_in_brasilia().date()
    recurrence = _create_recurrence(
        client,
        headers,
        "expense",
        "400.00",
        today,
    ).json()
    client.patch(f"/api/recurrences/{recurrence['id']}/pause", headers=headers)

    response = client.get("/api/reports/balance-prediction", headers=headers)

    assert response.status_code == 200
    assert response.json()["expected_future_recurring_expense"] == "0.00"


def test_prediction_is_isolated_by_user_and_updates_dynamically(client):
    first_headers = _register_and_login(client, "Primeira Previsao", "prediction-first@example.com")
    second_headers = _register_and_login(client, "Segunda Previsao", "prediction-second@example.com")
    today = now_in_brasilia().date()
    _create_transaction(client, second_headers, "expense", "900.00", today)

    before = client.get("/api/reports/balance-prediction", headers=first_headers).json()
    _create_transaction(client, first_headers, "expense", "50.00", today)
    after = client.get("/api/reports/balance-prediction", headers=first_headers).json()

    assert before["current_expense"] == "0.00"
    assert after["current_expense"] == "50.00"
    assert after["predicted_end_balance"] == "-50.00"
