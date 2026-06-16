from sqlalchemy import func, select

from models.budget_alert import BudgetAlert
from models.budget_limit import BudgetLimit
from models.category import Category
from models.recurrence import Recurrence
from models.revoked_token import RevokedToken
from models.survival_setting import SurvivalSetting
from models.transaction import Transaction
from models.user import User


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


def test_account_deletion_requires_authentication(client):
    response = client.request(
        "DELETE",
        "/api/settings/account",
        json={"current_password": "Senha@123"},
    )

    assert response.status_code == 401


def test_account_deletion_rejects_incorrect_password(client):
    headers = _register_and_login(client, "Conta Protegida", "protected-account@example.com")

    response = client.request(
        "DELETE",
        "/api/settings/account",
        headers=headers,
        json={"current_password": "senha-incorreta"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Current password is incorrect."
    assert client.get("/api/auth/me", headers=headers).status_code == 200


def test_account_deletion_rejects_password_above_bcrypt_byte_limit(client):
    headers = _register_and_login(client, "Conta Protegida", "protected-bytes@example.com")

    response = client.request(
        "DELETE",
        "/api/settings/account",
        headers=headers,
        json={"current_password": "á" * 40},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Current password is incorrect."
    assert client.get("/api/auth/me", headers=headers).status_code == 200


def test_account_deletion_removes_user_data_and_preserves_other_users(
    client,
    testing_session_local,
):
    deleted_headers = _register_and_login(client, "Conta Excluida", "deleted@example.com")
    preserved_headers = _register_and_login(client, "Conta Preservada", "preserved@example.com")

    category = client.post(
        "/api/categories/",
        headers=deleted_headers,
        json={"name": "Categoria privada", "type": "expense"},
    ).json()
    client.post(
        "/api/transactions/",
        headers=deleted_headers,
        json={
            "type": "expense",
            "amount": "100.00",
            "date": "2026-06-11",
            "category_id": category["id"],
        },
    )
    client.post(
        "/api/recurrences/",
        headers=deleted_headers,
        json={
            "type": "expense",
            "amount": "100.00",
            "start_date": "2026-06-11",
        },
    )
    client.put(
        "/api/settings/budget",
        headers=deleted_headers,
        json={"global_limit": "1000.00"},
    )
    client.get("/api/settings/budget/alert", headers=deleted_headers)
    client.put(
        "/api/settings/survival-mode",
        headers=deleted_headers,
        json={"activation_percentage": 70},
    )
    client.post("/api/auth/logout", headers=deleted_headers)

    deleted_headers = _register_and_login(client, "Conta Excluida", "deleted@example.com")
    response = client.request(
        "DELETE",
        "/api/settings/account",
        headers=deleted_headers,
        json={"current_password": "Senha@123"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Account and all associated data were permanently deleted."
    )
    assert client.get("/api/auth/me", headers=deleted_headers).status_code == 401
    assert client.get("/api/auth/me", headers=preserved_headers).status_code == 200

    with testing_session_local() as db:
        assert db.scalar(select(func.count(User.id)).where(User.email == "deleted@example.com")) == 0
        for model in (
            Transaction,
            Recurrence,
            BudgetLimit,
            BudgetAlert,
            SurvivalSetting,
            RevokedToken,
        ):
            assert db.scalar(select(func.count(model.id))) == 0
        assert db.scalar(
            select(func.count(Category.id)).where(Category.name == "Categoria privada")
        ) == 0
        assert db.scalar(select(func.count(User.id)).where(User.email == "preserved@example.com")) == 1
        assert db.scalar(
            select(func.count(Category.id)).where(
                Category.is_default.is_(True),
                Category.user_id.is_(None),
            )
        ) > 0


def test_deleted_email_can_be_registered_again(client):
    headers = _register_and_login(client, "Conta Recriavel", "recreate@example.com")
    client.request(
        "DELETE",
        "/api/settings/account",
        headers=headers,
        json={"current_password": "Senha@123"},
    )

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Conta Recriada",
            "email": "recreate@example.com",
            "password": "Senha@123",
        },
    )

    assert response.status_code == 201
