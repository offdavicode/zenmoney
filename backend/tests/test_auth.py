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
    assert logout_response.json()["message"] == "Logout completed successfully."

    revoked_response = client.get("/api/auth/me", headers=headers)
    assert revoked_response.status_code == 401
    assert revoked_response.json()["detail"] == "Token has been revoked."


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
    assert blocked_response.json()["detail"] == "Access temporarily blocked. Try again later."
