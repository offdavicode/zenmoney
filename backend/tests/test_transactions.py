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


def test_authenticated_user_can_create_list_update_and_delete_transactions(client):
    token = _register_and_login(client, "Marina Lima", "marina@example.com")
    headers = {"Authorization": f"Bearer {token}"}

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
            "emotion": "",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["amount"] == "75.50"
    assert update_response.json()["description"] == "Feira e mercado"
    assert update_response.json()["emotion"] == "not_specified"

    delete_response = client.delete(f"/api/transactions/{transaction_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/transactions/{transaction_id}", headers=headers)
    assert missing_response.status_code == 404


def test_user_cannot_access_another_users_transaction(client):
    first_token = _register_and_login(client, "Usuario A", "a@example.com")
    second_token = _register_and_login(client, "Usuario B", "b@example.com")

    first_headers = {"Authorization": f"Bearer {first_token}"}
    second_headers = {"Authorization": f"Bearer {second_token}"}

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


def test_transactions_require_authentication(client):
    response = client.get("/api/transactions/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided."
