import pytest


def _register_and_login(client, name: str, email: str, password: str = "Senha@123") -> str:
    client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    return login_response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _find_emotion_item(report: list[dict], emotion: str) -> dict:
    return next(item for item in report if item["emotion"] == emotion)


def _find_category_item(report: list[dict], category_name: str) -> dict:
    return next(item for item in report if item["category_name"] == category_name)


def _find_trigger_item(report: list[dict], emotion: str, category_name: str) -> dict:
    return next(
        item
        for item in report
        if item["emotion"] == emotion and item["category_name"] == category_name
    )


def _get_category_by_name(client, headers: dict[str, str], name: str) -> dict:
    response = client.get("/api/categories/", headers=headers)
    assert response.status_code == 200
    return next(category for category in response.json() if category["name"] == name)


def _create_expense_category(client, headers: dict[str, str], name: str) -> int:
    response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": name,
            "type": "expense",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/reports/summary",
        "/api/reports/by-emotion",
        "/api/reports/by-category",
        "/api/reports/triggers",
    ],
)
def test_reports_require_authentication(client, path):
    response = client.get(path)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided."


def test_summary_report_returns_zeroed_values_without_transactions(client):
    token = _register_and_login(client, "Igor Ramos", "igor@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/reports/summary", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_count"] == 0
    assert data["income_count"] == 0
    assert data["expense_count"] == 0
    assert data["total_income"] == "0.00"
    assert data["total_expense"] == "0.00"
    assert data["balance"] == "0.00"
    assert data["average_expense"] == "0.00"
    assert data["essential_expense"] == "0.00"
    assert data["essential_expense_percentage"] == 0.0
    assert data["non_essential_expense"] == "0.00"
    assert data["non_essential_expense_percentage"] == 0.0
    assert data["uncategorized_expense"] == "0.00"


def test_summary_report_aggregates_only_authenticated_user_transactions(client):
    first_token = _register_and_login(client, "Joana Freitas", "joana@example.com")
    second_token = _register_and_login(client, "Kaique Souza", "kaique@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    alimentacao = _get_category_by_name(client, first_headers, "Alimentacao")
    lazer = _get_category_by_name(client, first_headers, "Lazer")
    second_alimentacao = _get_category_by_name(client, second_headers, "Alimentacao")

    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "income",
            "amount": "1000.00",
            "date": "2026-06-01",
            "emotion": "felicidade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "category_id": alimentacao["id"],
            "type": "expense",
            "amount": "100.00",
            "date": "2026-06-01",
            "emotion": "ansiedade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "category_id": lazer["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-06-01",
            "emotion": "empolgacao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "expense",
            "amount": "25.00",
            "date": "2026-06-01",
            "emotion": "frustracao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=second_headers,
        json={
            "category_id": second_alimentacao["id"],
            "type": "expense",
            "amount": "500.00",
            "date": "2026-06-01",
            "emotion": "estresse",
        },
    )

    response = client.get("/api/reports/summary", headers=first_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_count"] == 4
    assert data["income_count"] == 1
    assert data["expense_count"] == 3
    assert data["total_income"] == "1000.00"
    assert data["total_expense"] == "175.00"
    assert data["balance"] == "825.00"
    assert data["average_expense"] == "58.33"
    assert data["essential_expense"] == "100.00"
    assert data["essential_expense_percentage"] == 57.14
    assert data["non_essential_expense"] == "75.00"
    assert data["non_essential_expense_percentage"] == 42.86
    assert data["uncategorized_expense"] == "25.00"


def test_emotion_report_returns_zeroed_items_without_expenses(client):
    token = _register_and_login(client, "Laura Maia", "laura@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/reports/by-emotion", headers=headers)

    assert response.status_code == 200
    report = response.json()
    assert report
    assert all(item["transaction_count"] == 0 for item in report)
    assert all(item["total_amount"] == "0.00" for item in report)
    assert all(item["percentage"] == 0.0 for item in report)


def test_emotion_report_groups_only_authenticated_user_expenses(client):
    first_token = _register_and_login(client, "Mateus Alves", "mateus@example.com")
    second_token = _register_and_login(client, "Nina Torres", "nina@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "expense",
            "amount": "100.00",
            "date": "2026-05-29",
            "emotion": "ansiedade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "expense",
            "amount": "50.00",
            "date": "2026-05-29",
            "emotion": "felicidade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "income",
            "amount": "1000.00",
            "date": "2026-05-29",
            "emotion": "felicidade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=second_headers,
        json={
            "type": "expense",
            "amount": "500.00",
            "date": "2026-05-29",
            "emotion": "frustracao",
        },
    )

    response = client.get("/api/reports/by-emotion", headers=first_headers)

    assert response.status_code == 200
    report = response.json()

    ansiedade = _find_emotion_item(report, "ansiedade")
    felicidade = _find_emotion_item(report, "felicidade")
    frustracao = _find_emotion_item(report, "frustracao")

    assert ansiedade["transaction_count"] == 1
    assert ansiedade["total_amount"] == "100.00"
    assert ansiedade["percentage"] == 66.67

    assert felicidade["transaction_count"] == 1
    assert felicidade["total_amount"] == "50.00"
    assert felicidade["percentage"] == 33.33

    assert frustracao["transaction_count"] == 0
    assert frustracao["total_amount"] == "0.00"
    assert frustracao["percentage"] == 0.0


def test_category_report_groups_only_authenticated_user_expenses(client):
    first_token = _register_and_login(client, "Otavio Lima", "otavio@example.com")
    second_token = _register_and_login(client, "Patricia Melo", "patricia@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    alimentacao = _get_category_by_name(client, first_headers, "Alimentacao")
    pet_shop_id = _create_expense_category(client, first_headers, "Pet shop")
    second_user_category_id = _get_category_by_name(client, second_headers, "Alimentacao")["id"]

    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "category_id": alimentacao["id"],
            "type": "expense",
            "amount": "100.00",
            "date": "2026-05-29",
            "emotion": "ansiedade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "category_id": pet_shop_id,
            "type": "expense",
            "amount": "50.00",
            "date": "2026-05-29",
            "emotion": "empolgacao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "expense",
            "amount": "25.00",
            "date": "2026-05-29",
            "emotion": "frustracao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "income",
            "amount": "1000.00",
            "date": "2026-05-29",
            "emotion": "felicidade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=second_headers,
        json={
            "category_id": second_user_category_id,
            "type": "expense",
            "amount": "500.00",
            "date": "2026-05-29",
            "emotion": "estresse",
        },
    )

    response = client.get("/api/reports/by-category", headers=first_headers)

    assert response.status_code == 200
    report = response.json()

    alimentacao_item = _find_category_item(report, "Alimentacao")
    pet_shop_item = _find_category_item(report, "Pet shop")
    uncategorized_item = _find_category_item(report, "Sem categoria")

    assert alimentacao_item["transaction_count"] == 1
    assert alimentacao_item["total_amount"] == "100.00"
    assert alimentacao_item["percentage"] == 57.14

    assert pet_shop_item["transaction_count"] == 1
    assert pet_shop_item["total_amount"] == "50.00"
    assert pet_shop_item["percentage"] == 28.57

    assert uncategorized_item["transaction_count"] == 1
    assert uncategorized_item["total_amount"] == "25.00"
    assert uncategorized_item["percentage"] == 14.29


def test_category_report_returns_zeroed_categories_without_expenses(client):
    token = _register_and_login(client, "Renata Lopes", "renata@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/reports/by-category", headers=headers)

    assert response.status_code == 200
    report = response.json()
    assert _find_category_item(report, "Sem categoria")["total_amount"] == "0.00"
    assert _find_category_item(report, "Alimentacao")["transaction_count"] == 0
    assert all(item["percentage"] == 0.0 for item in report)


def test_spending_triggers_cross_emotion_and_category(client):
    first_token = _register_and_login(client, "Sofia Castro", "sofia@example.com")
    second_token = _register_and_login(client, "Tiago Neves", "tiago@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    alimentacao = _get_category_by_name(client, first_headers, "Alimentacao")
    lazer = _get_category_by_name(client, first_headers, "Lazer")
    second_alimentacao = _get_category_by_name(client, second_headers, "Alimentacao")

    for amount in ("100.00", "50.00"):
        client.post(
            "/api/transactions/",
            headers=first_headers,
            json={
                "category_id": alimentacao["id"],
                "type": "expense",
                "amount": amount,
                "date": "2026-05-29",
                "emotion": "ansiedade",
            },
        )

    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "category_id": lazer["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-05-29",
            "emotion": "empolgacao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "expense",
            "amount": "25.00",
            "date": "2026-05-29",
            "emotion": "frustracao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=second_headers,
        json={
            "category_id": second_alimentacao["id"],
            "type": "expense",
            "amount": "999.00",
            "date": "2026-05-29",
            "emotion": "ansiedade",
        },
    )

    response = client.get("/api/reports/triggers", headers=first_headers)

    assert response.status_code == 200
    report = response.json()

    ansiedade_alimentacao = _find_trigger_item(report, "ansiedade", "Alimentacao")
    empolgacao_lazer = _find_trigger_item(report, "empolgacao", "Lazer")
    frustracao_sem_categoria = _find_trigger_item(report, "frustracao", "Sem categoria")

    assert ansiedade_alimentacao["transaction_count"] == 2
    assert ansiedade_alimentacao["total_amount"] == "150.00"
    assert ansiedade_alimentacao["average_amount"] == "75.00"
    assert ansiedade_alimentacao["percentage"] == 66.67

    assert empolgacao_lazer["transaction_count"] == 1
    assert empolgacao_lazer["total_amount"] == "50.00"
    assert empolgacao_lazer["percentage"] == 22.22

    assert frustracao_sem_categoria["transaction_count"] == 1
    assert frustracao_sem_categoria["total_amount"] == "25.00"
    assert frustracao_sem_categoria["percentage"] == 11.11


def test_spending_triggers_return_empty_list_without_expenses(client):
    token = _register_and_login(client, "Vitor Araujo", "vitor@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/reports/triggers", headers=headers)

    assert response.status_code == 200
    assert response.json() == []
