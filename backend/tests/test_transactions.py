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


def test_authenticated_user_can_create_list_update_and_delete_transactions(client):
    token = _register_and_login(client, "Marina Lima", "marina@example.com")
    headers = _auth_headers(token)

    create_response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "59.90",
            "date": "2026-05-24",
            "description": " Mercado da semana ",
            "emotion": "ansiedade",
        },
    )

    assert create_response.status_code == 201
    created_transaction = create_response.json()
    assert created_transaction["type"] == "expense"
    assert created_transaction["is_recurring"] is False
    assert created_transaction["registered_at"].endswith("-03:00")
    assert created_transaction["description"] == "Mercado da semana"
    assert created_transaction["emotion"] == "ansiedade"

    list_response = client.get("/api/transactions/", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    transaction_id = created_transaction["id"]

    get_response = client.get(f"/api/transactions/{transaction_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == transaction_id

    update_response = client.put(
        f"/api/transactions/{transaction_id}",
        headers=headers,
        json={
            "amount": "75.50",
            "description": "Feira e mercado",
            "emotion": "calma",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == "75.50"
    assert update_response.json()["description"] == "Feira e mercado"
    assert update_response.json()["emotion"] == "calma"
    assert update_response.json()["registered_at"] == created_transaction["registered_at"]

    delete_response = client.delete(f"/api/transactions/{transaction_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/transactions/{transaction_id}", headers=headers)
    assert missing_response.status_code == 404


def test_user_cannot_access_another_users_transaction(client):
    first_token = _register_and_login(client, "Usuario A", "a@example.com")
    second_token = _register_and_login(client, "Usuario B", "b@example.com")

    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    create_response = client.post(
        "/api/transactions/",
        headers=first_headers,
        json={
            "type": "income",
            "amount": "1500.00",
            "date": "2026-05-24",
            "description": "Freela",
            "emotion": "felicidade",
        },
    )
    transaction_id = create_response.json()["id"]

    forbidden_get_response = client.get(
        f"/api/transactions/{transaction_id}",
        headers=second_headers,
    )
    assert forbidden_get_response.status_code == 404
    assert forbidden_get_response.json()["detail"] == "Transaction not found."


def test_income_preserves_emotion(client):
    token = _register_and_login(client, "Receita Sem Emocao", "receita@example.com")
    headers = _auth_headers(token)

    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "income",
            "amount": "1500.00",
            "date": "2026-06-06",
            "emotion": "felicidade",
        },
    )

    assert response.status_code == 201
    assert response.json()["emotion"] == "felicidade"


def test_changing_expense_to_income_preserves_emotion(client):
    token = _register_and_login(client, "Mudanca de Tipo", "mudanca@example.com")
    headers = _auth_headers(token)

    create_response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "50.00",
            "date": "2026-06-06",
            "emotion": "ansiedade",
        },
    )

    update_response = client.put(
        f"/api/transactions/{create_response.json()['id']}",
        headers=headers,
        json={"type": "income"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["type"] == "income"
    assert update_response.json()["emotion"] == "ansiedade"


def test_transactions_require_authentication(client):
    response = client.get("/api/transactions/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided."


def test_transaction_can_use_default_category(client):
    token = _register_and_login(client, "Paula Mendes", "paula@example.com")
    headers = _auth_headers(token)
    category = _get_category_by_name(client, headers, "Alimentacao")

    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "category_id": category["id"],
            "type": "expense",
            "amount": "120.00",
            "date": "2026-05-29",
            "description": "Compras do mes",
            "emotion": "calma",
        },
    )

    assert response.status_code == 201
    assert response.json()["category_id"] == category["id"]


def test_transaction_can_use_user_category(client):
    token = _register_and_login(client, "Bruno Reis", "bruno@example.com")
    headers = _auth_headers(token)

    category_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "Pet shop",
            "type": "expense",
        },
    )
    category_id = category_response.json()["id"]

    transaction_response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "category_id": category_id,
            "type": "expense",
            "amount": "89.90",
            "date": "2026-05-29",
            "emotion": "calma",
        },
    )

    assert transaction_response.status_code == 201
    assert transaction_response.json()["category_id"] == category_id


def test_transaction_rejects_incompatible_category_type(client):
    token = _register_and_login(client, "Clara Dias", "clara@example.com")
    headers = _auth_headers(token)
    income_category = _get_category_by_name(client, headers, "Salario")

    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "category_id": income_category["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-05-29",
            "emotion": "calma",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found or incompatible with the transaction type."


def test_user_cannot_use_another_users_category_in_transaction(client):
    first_token = _register_and_login(client, "Dono Categoria", "dono@example.com")
    second_token = _register_and_login(client, "Outro Usuario", "outro@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)

    category_response = client.post(
        "/api/categories/",
        headers=first_headers,
        json={
            "name": "Assinaturas",
            "type": "expense",
        },
    )
    category_id = category_response.json()["id"]

    response = client.post(
        "/api/transactions/",
        headers=second_headers,
        json={
            "category_id": category_id,
            "type": "expense",
            "amount": "39.90",
            "date": "2026-05-29",
            "emotion": "calma",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found or incompatible with the transaction type."


def test_transaction_update_rejects_type_that_conflicts_with_current_category(client):
    token = _register_and_login(client, "Edu Nunes", "edu@example.com")
    headers = _auth_headers(token)
    category = _get_category_by_name(client, headers, "Alimentacao")

    create_response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "category_id": category["id"],
            "type": "expense",
            "amount": "75.00",
            "date": "2026-05-29",
            "emotion": "calma",
        },
    )
    transaction_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/transactions/{transaction_id}",
        headers=headers,
        json={"type": "income"},
    )

    assert update_response.status_code == 404
    assert update_response.json()["detail"] == "Category not found or incompatible with the transaction type."


def test_transaction_category_can_be_removed_on_update(client):
    token = _register_and_login(client, "Fernanda Rocha", "fernanda@example.com")
    headers = _auth_headers(token)
    category = _get_category_by_name(client, headers, "Alimentacao")

    create_response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "category_id": category["id"],
            "type": "expense",
            "amount": "30.00",
            "date": "2026-05-29",
            "emotion": "calma",
        },
    )
    transaction_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/transactions/{transaction_id}",
        headers=headers,
        json={"category_id": None},
    )

    assert update_response.status_code == 200
    assert update_response.json()["category_id"] is None


def test_transaction_normalizes_emotion_before_saving(client):
    token = _register_and_login(client, "Gisele Moraes", "gisele@example.com")
    headers = _auth_headers(token)

    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "22.50",
            "date": "2026-05-29",
            "emotion": " ANSIEDADE ",
        },
    )

    assert response.status_code == 201
    assert response.json()["emotion"] == "ansiedade"


def test_transaction_rejects_unknown_emotion(client):
    token = _register_and_login(client, "Helena Prado", "helena@example.com")
    headers = _auth_headers(token)

    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "22.50",
            "date": "2026-05-29",
            "emotion": "desconhecida",
        },
    )

    assert response.status_code == 422


def test_transaction_requires_selectable_emotion(client):
    token = _register_and_login(client, "Emocao Obrigatoria", "emotion-required@example.com")
    headers = _auth_headers(token)

    missing = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "income",
            "amount": "100.00",
            "date": "2026-06-10",
        },
    )
    blank = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "income",
            "amount": "100.00",
            "date": "2026-06-10",
            "emotion": "",
        },
    )
    not_specified = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "income",
            "amount": "100.00",
            "date": "2026-06-10",
            "emotion": "not_specified",
        },
    )

    assert missing.status_code == 422
    assert blank.status_code == 422
    assert not_specified.status_code == 422


def test_emotion_options_endpoint_returns_allowed_values(client):
    response = client.get("/api/transactions/emotions")

    assert response.status_code == 200
    values = {option["value"] for option in response.json()}
    assert "not_specified" not in values
    assert "calma" in values
    assert "ansiedade" in values
    assert "felicidade" in values
    assert "tedio" in values
    assert "culpa" not in values
    assert "impulso" not in values
