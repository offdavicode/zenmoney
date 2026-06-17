from datetime import date

from utils.date_utils import now_in_brasilia
from utils.recurrence_dates import (
    first_scheduled_on_or_after,
    next_scheduled_date,
    scheduled_date,
)


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


def _create_recurrence(client, headers: dict[str, str], **overrides):
    payload = {
        "type": "expense",
        "amount": "120.00",
        "description": "Assinatura mensal",
        "emotion": "indiferenca",
        "start_date": "2025-01-31",
        "day_of_month": 31,
    }
    payload.update(overrides)
    return client.post("/api/recurrences/", headers=headers, json=payload)


def test_calendar_helpers_handle_short_months():
    assert scheduled_date(2025, 2, 31) == date(2025, 2, 28)
    assert scheduled_date(2024, 2, 31) == date(2024, 2, 29)
    assert first_scheduled_on_or_after(date(2025, 2, 28), 31) == date(2025, 2, 28)
    assert next_scheduled_date(date(2025, 1, 31), 31) == date(2025, 2, 28)
    assert next_scheduled_date(date(2025, 2, 28), 31) == date(2025, 3, 31)


def test_creation_only_saves_schedule_until_run_due(client):
    headers = _register_and_login(client, "Recorrencia Salva", "rec-save@example.com")

    response = _create_recurrence(client, headers)

    assert response.status_code == 201
    assert response.json()["next_run_date"] == "2025-01-31"
    assert response.json()["status"] == "active"
    transactions = client.get("/api/transactions/", headers=headers)
    assert transactions.status_code == 200
    assert transactions.json() == []


def test_creation_infers_day_and_moves_to_next_month_when_needed(client):
    headers = _register_and_login(client, "Dia Inferido", "rec-inferred-day@example.com")

    inferred = _create_recurrence(
        client,
        headers,
        start_date="2026-06-20",
        day_of_month=None,
    )
    next_month = _create_recurrence(
        client,
        headers,
        start_date="2026-06-20",
        day_of_month=15,
    )

    assert inferred.status_code == 201
    assert inferred.json()["day_of_month"] == 20
    assert inferred.json()["next_run_date"] == "2026-06-20"
    assert next_month.status_code == 201
    assert next_month.json()["next_run_date"] == "2026-07-15"


def test_run_due_generates_all_due_occurrences_without_duplicates(client):
    headers = _register_and_login(client, "Execucao Recorrente", "rec-run@example.com")
    recurrence = _create_recurrence(
        client,
        headers,
        end_date="2025-03-31",
    ).json()

    first_run = client.post("/api/recurrences/run-due", headers=headers)

    assert first_run.status_code == 200
    assert first_run.json()["generated_count"] == 3
    assert [
        transaction["date"]
        for transaction in first_run.json()["generated_transactions"]
    ] == ["2025-01-31", "2025-02-28", "2025-03-31"]
    assert {
        transaction["recurrence_id"]
        for transaction in first_run.json()["generated_transactions"]
    } == {recurrence["id"]}
    assert all(
        transaction["is_recurring"] is True
        for transaction in first_run.json()["generated_transactions"]
    )

    second_run = client.post("/api/recurrences/run-due", headers=headers)
    assert second_run.status_code == 200
    assert second_run.json()["generated_count"] == 0

    stored = client.get(f"/api/recurrences/{recurrence['id']}", headers=headers).json()
    assert stored["is_active"] is False
    assert stored["status"] == "completed"
    assert stored["next_run_date"] == "2025-04-30"


def test_pause_prevents_generation_and_resume_skips_paused_period(client):
    headers = _register_and_login(client, "Pausa Recorrente", "rec-pause@example.com")
    recurrence = _create_recurrence(client, headers).json()

    pause_response = client.patch(
        f"/api/recurrences/{recurrence['id']}/pause",
        headers=headers,
    )
    assert pause_response.status_code == 200
    assert pause_response.json()["is_active"] is False
    assert pause_response.json()["status"] == "paused"

    run_response = client.post("/api/recurrences/run-due", headers=headers)
    assert run_response.json()["generated_count"] == 0

    resume_response = client.patch(
        f"/api/recurrences/{recurrence['id']}/resume",
        headers=headers,
    )
    assert resume_response.status_code == 200
    assert resume_response.json()["is_active"] is True
    assert date.fromisoformat(resume_response.json()["next_run_date"]) >= now_in_brasilia().date()


def test_resuming_active_recurrence_does_not_skip_due_occurrences(client):
    headers = _register_and_login(client, "Retomada Idempotente", "rec-resume-active@example.com")
    recurrence = _create_recurrence(client, headers).json()

    resume_response = client.patch(
        f"/api/recurrences/{recurrence['id']}/resume",
        headers=headers,
    )

    assert resume_response.status_code == 200
    assert resume_response.json()["next_run_date"] == "2025-01-31"

    run_response = client.post("/api/recurrences/run-due", headers=headers)
    assert run_response.json()["generated_count"] > 1
    assert run_response.json()["generated_transactions"][0]["date"] == "2025-01-31"


def test_no_op_schedule_update_does_not_skip_due_occurrences(client):
    headers = _register_and_login(client, "Edicao Idempotente", "rec-no-op@example.com")
    recurrence = _create_recurrence(client, headers).json()

    update_response = client.put(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
        json={"day_of_month": 31, "frequency": "monthly"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["next_run_date"] == "2025-01-31"


def test_setting_past_end_date_deactivates_recurrence_without_changing_history(client):
    headers = _register_and_login(client, "Encerramento Recorrente", "rec-end@example.com")
    recurrence = _create_recurrence(client, headers).json()

    update_response = client.put(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
        json={"end_date": "2025-03-31"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False
    assert date.fromisoformat(update_response.json()["next_run_date"]) > date(2025, 3, 31)
    assert client.get("/api/transactions/", headers=headers).json() == []


def test_completed_recurrence_cannot_be_resumed(client):
    headers = _register_and_login(client, "Fim Recorrencia", "rec-completed@example.com")
    recurrence = _create_recurrence(
        client,
        headers,
        end_date="2025-01-31",
    ).json()
    client.post("/api/recurrences/run-due", headers=headers)

    response = client.patch(
        f"/api/recurrences/{recurrence['id']}/resume",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Recurrence cannot be resumed because no future occurrence "
        "exists before its end date."
    )


def test_paused_recurrence_with_expired_end_date_is_reported_as_completed(client):
    headers = _register_and_login(client, "Pausa Expirada", "rec-expired-pause@example.com")
    recurrence = _create_recurrence(
        client,
        headers,
        end_date="2025-01-31",
    ).json()

    response = client.patch(
        f"/api/recurrences/{recurrence['id']}/pause",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["status"] == "completed"


def test_completed_recurrence_can_be_extended_and_resumed(client):
    headers = _register_and_login(client, "Extensao Recorrente", "rec-extend@example.com")
    recurrence = _create_recurrence(
        client,
        headers,
        end_date="2025-01-31",
    ).json()
    client.post("/api/recurrences/run-due", headers=headers)

    update_response = client.put(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
        json={"end_date": None},
    )
    resume_response = client.patch(
        f"/api/recurrences/{recurrence['id']}/resume",
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "paused"
    assert resume_response.status_code == 200
    assert resume_response.json()["status"] == "active"


def test_editing_recurrence_does_not_change_generated_transactions(client):
    headers = _register_and_login(client, "Edicao Recorrente", "rec-edit@example.com")
    recurrence = _create_recurrence(
        client,
        headers,
        amount="80.00",
        end_date="2025-01-31",
    ).json()
    client.post("/api/recurrences/run-due", headers=headers)

    update_response = client.put(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
        json={"amount": "150.00", "description": "Novo valor"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["amount"] == "150.00"
    transactions = client.get("/api/transactions/", headers=headers).json()
    assert len(transactions) == 1
    assert transactions[0]["amount"] == "80.00"
    assert transactions[0]["description"] == "Assinatura mensal"


def test_deleting_recurrence_preserves_generated_transactions(client):
    headers = _register_and_login(client, "Exclusao Recorrente", "rec-delete@example.com")
    recurrence = _create_recurrence(
        client,
        headers,
        end_date="2025-01-31",
    ).json()
    client.post("/api/recurrences/run-due", headers=headers)

    delete_response = client.delete(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    transactions = client.get("/api/transactions/", headers=headers).json()
    assert len(transactions) == 1
    assert transactions[0]["recurrence_id"] is None
    assert transactions[0]["is_recurring"] is True


def test_recurrence_validates_category_type_and_preserves_income_emotion(client):
    headers = _register_and_login(client, "Validacao Recorrente", "rec-validation@example.com")
    categories = client.get("/api/categories/", headers=headers).json()
    expense_category = next(category for category in categories if category["name"] == "Alimentacao")

    incompatible = _create_recurrence(
        client,
        headers,
        type="income",
        category_id=expense_category["id"],
    )
    assert incompatible.status_code == 404

    income = _create_recurrence(
        client,
        headers,
        type="income",
        category_id=None,
        emotion="felicidade",
    )
    assert income.status_code == 201
    assert income.json()["emotion"] == "felicidade"


def test_deleting_category_reclassifies_recurrence_as_unspecified(client):
    headers = _register_and_login(client, "Categoria Recorrente", "rec-category@example.com")
    categories = client.get("/api/categories/", headers=headers).json()
    unspecified = next(
        category
        for category in categories
        if category["name"] == "Nao especificado" and category["type"] == "expense"
    )
    category = client.post(
        "/api/categories/",
        headers=headers,
        json={"name": "Assinatura temporaria", "type": "expense"},
    ).json()
    recurrence = _create_recurrence(
        client,
        headers,
        category_id=category["id"],
    ).json()

    delete_response = client.delete(f"/api/categories/{category['id']}", headers=headers)
    stored_recurrence = client.get(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    assert stored_recurrence.json()["category_id"] == unspecified["id"]


def test_generated_transaction_is_included_in_reports(client):
    headers = _register_and_login(client, "Relatorio Recorrente", "rec-report@example.com")
    _create_recurrence(
        client,
        headers,
        amount="75.00",
        end_date="2025-01-31",
    )
    client.post("/api/recurrences/run-due", headers=headers)

    summary = client.get(
        "/api/reports/summary?month=2025-01",
        headers=headers,
    )

    assert summary.status_code == 200
    assert summary.json()["expense_count"] == 1
    assert summary.json()["total_expense"] == "75.00"


def test_recurrence_rejects_invalid_dates_and_null_required_updates(client):
    headers = _register_and_login(client, "Datas Recorrentes", "rec-date@example.com")

    invalid_range = _create_recurrence(
        client,
        headers,
        start_date="2025-03-31",
        end_date="2025-02-28",
    )
    assert invalid_range.status_code == 422

    no_occurrence = _create_recurrence(
        client,
        headers,
        start_date="2025-01-20",
        day_of_month=15,
        end_date="2025-01-31",
    )
    assert no_occurrence.status_code == 400

    recurrence = _create_recurrence(client, headers).json()
    null_update = client.put(
        f"/api/recurrences/{recurrence['id']}",
        headers=headers,
        json={"amount": None},
    )
    assert null_update.status_code == 422


def test_user_cannot_access_or_run_another_users_recurrence(client):
    first_headers = _register_and_login(client, "Dono Recorrencia", "rec-owner@example.com")
    second_headers = _register_and_login(client, "Outro Recorrencia", "rec-other@example.com")
    recurrence = _create_recurrence(
        client,
        first_headers,
        end_date="2025-01-31",
    ).json()

    get_response = client.get(
        f"/api/recurrences/{recurrence['id']}",
        headers=second_headers,
    )
    assert get_response.status_code == 404

    other_run = client.post("/api/recurrences/run-due", headers=second_headers)
    assert other_run.status_code == 200
    assert other_run.json()["generated_count"] == 0

    owner_run = client.post("/api/recurrences/run-due", headers=first_headers)
    assert owner_run.json()["generated_count"] == 1


def test_user_cannot_modify_another_users_recurrence(client):
    first_headers = _register_and_login(client, "Dono Protegido", "rec-protected-owner@example.com")
    second_headers = _register_and_login(client, "Outro Protegido", "rec-protected-other@example.com")
    recurrence = _create_recurrence(client, first_headers).json()
    recurrence_path = f"/api/recurrences/{recurrence['id']}"

    assert client.put(
        recurrence_path,
        headers=second_headers,
        json={"amount": "500.00"},
    ).status_code == 404
    assert client.patch(f"{recurrence_path}/pause", headers=second_headers).status_code == 404
    assert client.patch(f"{recurrence_path}/resume", headers=second_headers).status_code == 404
    assert client.delete(recurrence_path, headers=second_headers).status_code == 404


def test_recurrence_endpoints_require_authentication(client):
    assert client.get("/api/recurrences/").status_code == 401
    assert client.post("/api/recurrences/run-due").status_code == 401
