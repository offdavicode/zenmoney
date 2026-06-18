import pytest


def _register_and_login(client, name: str, email: str) -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "Senha@123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Senha@123"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _get_category(client, headers: dict[str, str], name: str) -> dict:
    response = client.get("/api/categories/", headers=headers)
    assert response.status_code == 200
    return next(item for item in response.json() if item["name"] == name)


def _create_category(
    client,
    headers: dict[str, str],
    name: str,
    is_essential: bool,
) -> dict:
    response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": name,
            "type": "expense",
            "is_essential": is_essential,
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_transaction(
    client,
    headers: dict[str, str],
    *,
    amount: str,
    transaction_date: str = "2026-06-09",
    category_id: int | None = None,
    transaction_type: str = "expense",
) -> dict:
    emotion = "felicidade" if transaction_type == "income" else "calma"
    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "category_id": category_id,
            "type": transaction_type,
            "amount": amount,
            "date": transaction_date,
            "emotion": emotion,
        },
    )
    assert response.status_code == 201
    return response.json()


def _set_budget(client, headers: dict[str, str], payload: dict) -> dict:
    response = client.put(
        "/api/settings/budget?month=2026-06",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/settings/survival-mode", None),
        ("put", "/api/settings/survival-mode", {"activation_percentage": 70}),
        ("get", "/api/reports/survival-mode?month=2026-06", None),
    ],
)
def test_survival_routes_require_authentication(client, method, path, payload):
    request = getattr(client, method)
    response = request(path, json=payload) if payload is not None else request(path)

    assert response.status_code == 401


def test_survival_setting_defaults_to_eighty_and_can_be_updated(client):
    headers = _register_and_login(client, "Ana Luz", "ana-survival@example.com")

    default_response = client.get("/api/settings/survival-mode", headers=headers)
    update_response = client.put(
        "/api/settings/survival-mode",
        headers=headers,
        json={"activation_percentage": 65},
    )
    second_update_response = client.put(
        "/api/settings/survival-mode",
        headers=headers,
        json={"activation_percentage": 90},
    )

    assert default_response.json() == {
        "activation_percentage": 80,
        "is_default": True,
    }
    assert update_response.json() == {
        "activation_percentage": 65,
        "is_default": False,
    }
    assert second_update_response.json() == {
        "activation_percentage": 90,
        "is_default": False,
    }


@pytest.mark.parametrize("activation_percentage", [49, 91])
def test_survival_setting_rejects_percentage_outside_allowed_range(
    client,
    activation_percentage,
):
    headers = _register_and_login(
        client,
        f"Usuario {activation_percentage}",
        f"survival-{activation_percentage}@example.com",
    )

    response = client.put(
        "/api/settings/survival-mode",
        headers=headers,
        json={"activation_percentage": activation_percentage},
    )

    assert response.status_code == 422


def test_survival_setting_is_isolated_between_users(client):
    first_headers = _register_and_login(client, "Bia Lima", "bia-survival@example.com")
    second_headers = _register_and_login(client, "Caio Lima", "caio-survival@example.com")
    client.put(
        "/api/settings/survival-mode",
        headers=first_headers,
        json={"activation_percentage": 55},
    )

    first_response = client.get("/api/settings/survival-mode", headers=first_headers)
    second_response = client.get("/api/settings/survival-mode", headers=second_headers)

    assert first_response.json()["activation_percentage"] == 55
    assert second_response.json() == {
        "activation_percentage": 80,
        "is_default": True,
    }


def test_survival_mode_is_inactive_without_limits(client):
    headers = _register_and_login(client, "Dora Luz", "dora-survival@example.com")
    _create_transaction(client, headers, amount="500.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "month": "2026-06",
        "activation_percentage": 80,
        "is_active": False,
        "activation_reason": "no_limits",
        "trigger": None,
        "recommendations": [],
        "highlighted_transaction_ids": [],
    }


def test_survival_mode_is_inactive_below_configured_threshold(client):
    headers = _register_and_login(client, "Eva Luz", "eva-survival@example.com")
    _set_budget(client, headers, {"global_limit": "1000.00"})
    _create_transaction(client, headers, amount="799.99")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["activation_reason"] == "below_threshold"


def test_survival_mode_activates_at_exact_global_threshold_and_recommends_only_non_essential(
    client,
):
    first_headers = _register_and_login(client, "Fabi Luz", "fabi-survival@example.com")
    second_headers = _register_and_login(client, "Gabi Luz", "gabi-survival@example.com")
    lazer = _get_category(client, first_headers, "Lazer")
    alimentacao = _get_category(client, first_headers, "Alimentacao")
    second_lazer = _get_category(client, second_headers, "Lazer")
    _set_budget(client, first_headers, {"global_limit": "1000.00"})

    lazer_transaction = _create_transaction(
        client,
        first_headers,
        category_id=lazer["id"],
        amount="300.00",
    )
    _create_transaction(
        client,
        first_headers,
        category_id=alimentacao["id"],
        amount="500.00",
    )
    _create_transaction(
        client,
        first_headers,
        category_id=lazer["id"],
        amount="900.00",
        transaction_date="2026-05-31",
    )
    _create_transaction(
        client,
        first_headers,
        amount="1000.00",
        transaction_type="income",
    )
    _create_transaction(
        client,
        second_headers,
        category_id=second_lazer["id"],
        amount="999.00",
    )

    response = client.get(
        "/api/reports/survival-mode?month=2026-06",
        headers=first_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["activation_reason"] == "global_limit"
    assert data["trigger"]["scope"] == "global"
    assert data["trigger"]["usage_percentage"] == 80.0
    assert [item["category_name"] for item in data["recommendations"]] == ["Lazer"]
    assert data["recommendations"][0]["spent_amount"] == "300.00"
    assert data["recommendations"][0]["suggest_block_new_transactions"] is True
    assert data["highlighted_transaction_ids"] == [lazer_transaction["id"]]


def test_survival_mode_activates_from_category_limit_without_global_limit(client):
    headers = _register_and_login(client, "Hugo Luz", "hugo-survival@example.com")
    lazer = _get_category(client, headers, "Lazer")
    _set_budget(
        client,
        headers,
        {
            "category_limits": [
                {"category_id": lazer["id"], "amount": "200.00"},
            ],
        },
    )
    _create_transaction(client, headers, category_id=lazer["id"], amount="170.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["activation_reason"] == "category_limit"
    assert data["trigger"]["category_name"] == "Lazer"
    assert data["trigger"]["usage_percentage"] == 85.0


def test_essential_category_limit_can_activate_mode_without_becoming_recommendation(client):
    headers = _register_and_login(client, "Helo Luz", "helo-survival@example.com")
    alimentacao = _get_category(client, headers, "Alimentacao")
    _set_budget(
        client,
        headers,
        {
            "category_limits": [
                {"category_id": alimentacao["id"], "amount": "100.00"},
            ],
        },
    )
    _create_transaction(client, headers, category_id=alimentacao["id"], amount="80.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["trigger"]["category_name"] == "Alimentacao"
    assert data["recommendations"] == []
    assert data["highlighted_transaction_ids"] == []


def test_survival_mode_reports_highest_usage_trigger(client):
    headers = _register_and_login(client, "Helio Luz", "helio-survival@example.com")
    lazer = _get_category(client, headers, "Lazer")
    _set_budget(
        client,
        headers,
        {
            "global_limit": "1000.00",
            "category_limits": [
                {"category_id": lazer["id"], "amount": "200.00"},
            ],
        },
    )
    _create_transaction(client, headers, category_id=lazer["id"], amount="180.00")
    _create_transaction(client, headers, amount="620.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["trigger"]["scope"] == "category"
    assert data["trigger"]["category_name"] == "Lazer"
    assert data["trigger"]["usage_percentage"] == 90.0


def test_survival_mode_uses_custom_activation_percentage(client):
    headers = _register_and_login(client, "Iara Luz", "iara-survival@example.com")
    client.put(
        "/api/settings/survival-mode",
        headers=headers,
        json={"activation_percentage": 90},
    )
    _set_budget(client, headers, {"global_limit": "1000.00"})
    _create_transaction(client, headers, amount="850.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    assert response.json()["activation_percentage"] == 90
    assert response.json()["is_active"] is False


def test_survival_recommendations_prioritize_exceeded_limit_then_usage_then_spending(client):
    headers = _register_and_login(client, "Jo Luz", "jo-survival@example.com")
    viagens = _create_category(client, headers, "Viagens pessoais", False)
    jogos = _create_category(client, headers, "Jogos", False)
    roupas = _get_category(client, headers, "Roupas")
    _set_budget(
        client,
        headers,
        {
            "category_limits": [
                {"category_id": viagens["id"], "amount": "100.00"},
                {"category_id": jogos["id"], "amount": "100.00"},
            ],
        },
    )
    _create_transaction(client, headers, category_id=viagens["id"], amount="160.00")
    _create_transaction(client, headers, category_id=jogos["id"], amount="150.00")
    _create_transaction(client, headers, category_id=roupas["id"], amount="500.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert [item["category_name"] for item in recommendations] == [
        "Viagens pessoais",
        "Jogos",
        "Roupas",
    ]
    assert recommendations[0]["exceeded_amount"] == "60.00"
    assert recommendations[1]["exceeded_amount"] == "50.00"
    assert recommendations[2]["limit_amount"] is None


def test_survival_recommendation_order_uses_exact_usage_when_displayed_percentages_tie(client):
    headers = _register_and_login(client, "Josi Luz", "josi-survival@example.com")
    first = _create_category(client, headers, "Primeira proporcao", False)
    second = _create_category(client, headers, "Segunda proporcao", False)
    _set_budget(
        client,
        headers,
        {
            "category_limits": [
                {"category_id": first["id"], "amount": "10000.00"},
                {"category_id": second["id"], "amount": "15000.00"},
            ],
        },
    )
    _create_transaction(client, headers, category_id=first["id"], amount="10001.00")
    _create_transaction(client, headers, category_id=second["id"], amount="15001.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    recommendations = response.json()["recommendations"]
    assert recommendations[0]["usage_percentage"] == recommendations[1]["usage_percentage"]
    assert [item["category_name"] for item in recommendations] == [
        "Primeira proporcao",
        "Segunda proporcao",
    ]


def test_active_survival_mode_can_return_no_recommendations_when_only_essential_expenses_exist(
    client,
):
    headers = _register_and_login(client, "Kai Luz", "kai-survival@example.com")
    alimentacao = _get_category(client, headers, "Alimentacao")
    _set_budget(client, headers, {"global_limit": "100.00"})
    _create_transaction(client, headers, category_id=alimentacao["id"], amount="90.00")

    response = client.get("/api/reports/survival-mode?month=2026-06", headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    assert response.json()["recommendations"] == []
    assert response.json()["highlighted_transaction_ids"] == []


def test_survival_mode_never_blocks_new_transactions(client):
    headers = _register_and_login(client, "Lia Luz", "lia-survival@example.com")
    lazer = _get_category(client, headers, "Lazer")
    _set_budget(client, headers, {"global_limit": "100.00"})
    _create_transaction(client, headers, category_id=lazer["id"], amount="100.00")
    active_response = client.get(
        "/api/reports/survival-mode?month=2026-06",
        headers=headers,
    )

    new_transaction = _create_transaction(
        client,
        headers,
        category_id=lazer["id"],
        amount="10.00",
    )

    assert active_response.json()["is_active"] is True
    assert new_transaction["amount"] == "10.00"


def test_survival_mode_rejects_invalid_month(client):
    headers = _register_and_login(client, "Mia Luz", "mia-survival@example.com")

    response = client.get("/api/reports/survival-mode?month=2026-13", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "O mês deve usar o formato AAAA-MM."
