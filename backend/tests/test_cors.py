import pytest


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)
def test_preflight_allows_configured_frontend_origins(client, origin):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "Authorization" in response.headers["access-control-allow-headers"]
    assert "Content-Type" in response.headers["access-control-allow-headers"]


def test_allowed_origin_receives_cors_header_on_regular_request(client):
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_preflight_rejects_unknown_origin(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "https://unknown.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_unknown_origin_does_not_receive_cors_header_on_regular_request(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://unknown.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
