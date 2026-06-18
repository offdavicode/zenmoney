import pytest


def test_register_login_me_and_logout_cycle(client):
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Maria Silva",
            "email": "maria@example.com",
            "password": "Senha@123",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json()["email"] == "maria@example.com"

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "maria@example.com",
            "password": "Senha@123",
        },
    )

    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["email"] == "maria@example.com"

    token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["name"] == "Maria Silva"

    profile_response = client.get("/api/settings/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "maria@example.com"

    logout_response = client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logout realizado com sucesso."

    revoked_response = client.get("/api/auth/me", headers=headers)
    assert revoked_response.status_code == 401
    assert revoked_response.json()["detail"] == "O token foi revogado."


@pytest.mark.parametrize(
    "password",
    [
        "senha@123",
        "SENHA@123",
        "Senha1234",
        "Senha@abc",
        "Se@1",
    ],
)
def test_register_rejects_passwords_that_do_not_match_frontend_rule(client, password):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Senha Invalida",
            "email": f"{password.replace('@', 'at')}@example.com",
            "password": password,
        },
    )

    assert response.status_code == 422


def test_authenticated_user_can_update_profile(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Ana Souza",
            "email": "ana@example.com",
            "password": "Senha@123",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "ana@example.com",
            "password": "Senha@123",
        },
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_response = client.put(
        "/api/settings/profile",
        headers=headers,
        json={
            "name": "Ana Paula Souza",
            "email": "ana.paula@example.com",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Ana Paula Souza"
    assert update_response.json()["email"] == "ana.paula@example.com"

    profile_response = client.get("/api/settings/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "ana.paula@example.com"


def test_authenticated_user_can_change_password(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Costa",
            "email": "lucas@example.com",
            "password": "Senha@123",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "Senha@123",
        },
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    change_password_response = client.put(
        "/api/settings/password",
        headers=headers,
        json={
            "current_password": "Senha@123",
            "new_password": "NovaSenha@456",
        },
    )

    assert change_password_response.status_code == 200
    assert change_password_response.json()["message"] == "Senha atualizada com sucesso."

    old_login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "Senha@123",
        },
    )
    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "NovaSenha@456",
        },
    )
    assert new_login_response.status_code == 200


def test_profile_update_rejects_duplicate_email(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Primeiro Usuario",
            "email": "primeiro@example.com",
            "password": "Senha@123",
        },
    )
    client.post(
        "/api/auth/register",
        json={
            "name": "Segundo Usuario",
            "email": "segundo@example.com",
            "password": "Senha@123",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "segundo@example.com",
            "password": "Senha@123",
        },
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_response = client.put(
        "/api/settings/profile",
        headers=headers,
        json={"email": "primeiro@example.com"},
    )

    assert update_response.status_code == 409
    assert update_response.json()["detail"] == "Já existe um usuário cadastrado com este e-mail."


def test_login_is_temporarily_blocked_after_repeated_invalid_attempts(client):
    client.post(
        "/api/auth/register",
        json={
            "name": "Jose Lima",
            "email": "jose@example.com",
            "password": "Senha@123",
        },
    )

    for _ in range(5):
        client.post(
            "/api/auth/login",
            json={
                "email": "jose@example.com",
                "password": "senha-errada",
            },
        )

    blocked_response = client.post(
        "/api/auth/login",
        json={
            "email": "jose@example.com",
            "password": "Senha@123",
        },
    )

    assert blocked_response.status_code == 423
    assert blocked_response.json()["detail"] == "Acesso temporariamente bloqueado. Tente novamente mais tarde."
