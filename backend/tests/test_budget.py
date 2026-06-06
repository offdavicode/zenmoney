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


def _get_category_by_name(client, headers: dict[str, str], name: str) -> dict:
    response = client.get("/api/categories/", headers=headers)
    assert response.status_code == 200
    return next(category for category in response.json() if category["name"] == name)


def _find_category_limit(response_data: dict, category_name: str) -> dict:
    return next(item for item in response_data["category_limits"] if item["category_name"] == category_name)


def test_budget_routes_require_authentication(client):
    get_response = client.get("/api/settings/budget?month=2026-06")
    put_response = client.put(
        "/api/settings/budget?month=2026-06",
        json={"global_limit": "200.00"},
    )
    alert_response = client.get("/api/settings/budget/alert?month=2026-06")

    assert get_response.status_code == 401
    assert put_response.status_code == 401
    assert alert_response.status_code == 401


def test_budget_defaults_to_no_limits(client):
    token = _register_and_login(client, "Lais Martins", "lais@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/settings/budget?month=2026-06", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["month"] == "2026-06"
    assert data["global_limit"] is None
    assert data["category_limits"] == []
    assert data["alerts_enabled"] is False


def test_user_can_set_global_and_category_budget_limits(client):
    first_token = _register_and_login(client, "Marcos Nunes", "marcos@example.com")
    second_token = _register_and_login(client, "Nadia Sales", "nadia@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    alimentacao = _get_category_by_name(client, first_headers, "Alimentacao")
    lazer = _get_category_by_name(client, first_headers, "Lazer")
    second_alimentacao = _get_category_by_name(client, second_headers, "Alimentacao")

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
            "date": "2026-06-02",
            "emotion": "empolgacao",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "category_id": alimentacao["id"],
            "type": "expense",
            "amount": "999.00",
            "date": "2026-05-31",
            "emotion": "estresse",
        },
    )
    client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "income",
            "amount": "1000.00",
            "date": "2026-06-03",
            "emotion": "felicidade",
        },
    )
    client.post(
        "/api/transactions/",
        headers=second_headers,
        json={
            "category_id": second_alimentacao["id"],
            "type": "expense",
            "amount": "777.00",
            "date": "2026-06-01",
            "emotion": "frustracao",
        },
    )

    update_response = client.put(
        "/api/settings/budget?month=2026-06",
        headers=first_headers,
        json={
            "global_limit": "200.00",
            "category_limits": [
                {
                    "category_id": alimentacao["id"],
                    "amount": "120.00",
                },
                {
                    "category_id": lazer["id"],
                    "amount": "60.00",
                },
            ],
        },
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["alerts_enabled"] is True

    global_limit = data["global_limit"]
    assert global_limit["category_id"] is None
    assert global_limit["limit_amount"] == "200.00"
    assert global_limit["spent_amount"] == "150.00"
    assert global_limit["remaining_amount"] == "50.00"
    assert global_limit["usage_percentage"] == 75.0
    assert global_limit["is_exceeded"] is False

    alimentacao_limit = _find_category_limit(data, "Alimentacao")
    assert alimentacao_limit["limit_amount"] == "120.00"
    assert alimentacao_limit["spent_amount"] == "100.00"
    assert alimentacao_limit["remaining_amount"] == "20.00"
    assert alimentacao_limit["usage_percentage"] == 83.33

    lazer_limit = _find_category_limit(data, "Lazer")
    assert lazer_limit["limit_amount"] == "60.00"
    assert lazer_limit["spent_amount"] == "50.00"
    assert lazer_limit["remaining_amount"] == "10.00"
    assert lazer_limit["usage_percentage"] == 83.33

    get_response = client.get("/api/settings/budget?month=2026-06", headers=first_headers)
    assert get_response.status_code == 200
    assert get_response.json() == data


def test_budget_limit_can_be_removed(client):
    token = _register_and_login(client, "Olivia Costa", "olivia@example.com")
    headers = _auth_headers(token)
    alimentacao = _get_category_by_name(client, headers, "Alimentacao")

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={
            "global_limit": "200.00",
            "category_limits": [
                {
                    "category_id": alimentacao["id"],
                    "amount": "100.00",
                },
            ],
        },
    )

    remove_response = client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={
            "global_limit": None,
            "category_limits": [
                {
                    "category_id": alimentacao["id"],
                    "amount": None,
                },
            ],
        },
    )

    assert remove_response.status_code == 200
    data = remove_response.json()
    assert data["global_limit"] is None
    assert data["category_limits"] == []
    assert data["alerts_enabled"] is False


def test_budget_rejects_invalid_values_and_categories(client):
    token = _register_and_login(client, "Pedro Henrique", "pedro@example.com")
    headers = _auth_headers(token)
    salario = _get_category_by_name(client, headers, "Salario")

    zero_response = client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={"global_limit": "0.00"},
    )
    assert zero_response.status_code == 422

    income_category_response = client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={
            "category_limits": [
                {
                    "category_id": salario["id"],
                    "amount": "100.00",
                },
            ],
        },
    )
    assert income_category_response.status_code == 404
    assert (
        income_category_response.json()["detail"]
        == "Category not found or not available for expense budget."
    )


def test_budget_rejects_invalid_month(client):
    token = _register_and_login(client, "Quenia Rocha", "quenia@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/settings/budget?month=2026-13", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Month must use YYYY-MM format."


def test_budget_alert_returns_none_when_no_limit_or_threshold_was_reached(client):
    token = _register_and_login(client, "Rafael Alves", "rafael@example.com")
    headers = _auth_headers(token)

    no_limit_response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)
    assert no_limit_response.status_code == 200
    assert no_limit_response.json() == {"month": "2026-06", "alert": None}

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={"global_limit": "200.00"},
    )
    client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "19.99",
            "date": "2026-06-01",
            "emotion": "ansiedade",
        },
    )

    below_threshold_response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)
    assert below_threshold_response.status_code == 200
    assert below_threshold_response.json()["alert"] is None


def test_budget_alert_is_sent_once_for_highest_crossed_threshold(client):
    token = _register_and_login(client, "Silvia Bento", "silvia@example.com")
    headers = _auth_headers(token)

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={"global_limit": "200.00"},
    )
    client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "150.00",
            "date": "2026-06-01",
            "emotion": "estresse",
        },
    )

    first_response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)
    second_response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)

    assert first_response.status_code == 200
    alert = first_response.json()["alert"]
    assert alert["scope"] == "global"
    assert alert["category_id"] is None
    assert alert["threshold_percent"] == 70
    assert alert["spent_amount"] == "150.00"
    assert alert["usage_percentage"] == 75.0
    assert alert["message"] == "Voce atingiu 70% do limite mensal geral."

    assert second_response.status_code == 200
    assert second_response.json()["alert"] is None


def test_budget_alert_emits_next_threshold_after_more_spending(client):
    token = _register_and_login(client, "Tania Freire", "tania@example.com")
    headers = _auth_headers(token)

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={"global_limit": "200.00"},
    )
    client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "150.00",
            "date": "2026-06-01",
            "emotion": "estresse",
        },
    )
    client.get("/api/settings/budget/alert?month=2026-06", headers=headers)

    client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "20.00",
            "date": "2026-06-02",
            "emotion": "ansiedade",
        },
    )

    response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)

    assert response.status_code == 200
    alert = response.json()["alert"]
    assert alert["threshold_percent"] == 80
    assert alert["spent_amount"] == "170.00"
    assert alert["usage_percentage"] == 85.0


def test_budget_alert_returns_highest_alert_when_multiple_limits_cross_thresholds(client):
    token = _register_and_login(client, "Ulisses Paiva", "ulisses@example.com")
    headers = _auth_headers(token)
    alimentacao = _get_category_by_name(client, headers, "Alimentacao")

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={
            "global_limit": "200.00",
            "category_limits": [
                {
                    "category_id": alimentacao["id"],
                    "amount": "120.00",
                },
            ],
        },
    )
    client.post(
        "/api/transactions/",
        headers=headers,
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
        headers=headers,
        json={
            "type": "expense",
            "amount": "50.00",
            "date": "2026-06-02",
            "emotion": "frustracao",
        },
    )

    response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)

    assert response.status_code == 200
    alert = response.json()["alert"]
    assert alert["scope"] == "category"
    assert alert["category_id"] == alimentacao["id"]
    assert alert["category_name"] == "Alimentacao"
    assert alert["threshold_percent"] == 80
    assert alert["spent_amount"] == "100.00"
    assert alert["message"] == "Voce atingiu 80% do limite de Alimentacao."


def test_budget_alert_history_is_reset_when_limit_changes(client):
    token = _register_and_login(client, "Vivian Reis", "vivian@example.com")
    headers = _auth_headers(token)

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={"global_limit": "200.00"},
    )
    client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "150.00",
            "date": "2026-06-01",
            "emotion": "estresse",
        },
    )
    client.get("/api/settings/budget/alert?month=2026-06", headers=headers)

    client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json={"global_limit": "100.00"},
    )
    response = client.get("/api/settings/budget/alert?month=2026-06", headers=headers)

    assert response.status_code == 200
    alert = response.json()["alert"]
    assert alert["threshold_percent"] == 100
    assert alert["limit_amount"] == "100.00"
    assert alert["spent_amount"] == "150.00"
    assert alert["usage_percentage"] == 150.0
