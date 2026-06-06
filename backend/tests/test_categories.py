import pytest


def auth_headers(client, name="Carla Ramos", email="carla@example.com"):
    client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": "Senha@123",
        },
    )
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "Senha@123",
        },
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path", "json_payload"),
    [
        ("get", "/api/categories/", None),
        (
            "post",
            "/api/categories/",
            {
                "name": "Mercado",
                "type": "expense",
                "is_essential": True,
            },
        ),
        (
            "put",
            "/api/categories/1",
            {
                "name": "Supermercado",
            },
        ),
        ("delete", "/api/categories/1", None),
    ],
)
def test_category_routes_require_authentication(client, method, path, json_payload):
    request = getattr(client, method)
    response = request(path, json=json_payload) if json_payload is not None else request(path)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication credentials were not provided."


def test_authenticated_user_can_list_default_categories(client):
    headers = auth_headers(client)
    response = client.get("/api/categories/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    names = {category["name"] for category in data}
    assert "Alimentacao" in names
    assert "Moradia" in names
    assert "Salario" in names
    assert all(category["is_default"] is True for category in data)
    unspecified_categories = [
        category for category in data if category["name"] == "Nao especificado"
    ]
    assert {category["type"] for category in unspecified_categories} == {
        "income",
        "expense",
    }


def test_authenticated_user_can_create_subcategory(client):
    headers = auth_headers(client)
    categories_response = client.get("/api/categories/", headers=headers)
    moradia = next(
        category
        for category in categories_response.json()
        if category["name"] == "Moradia"
    )

    response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "Aluguel residencial",
            "type": "expense",
            "parent_id": moradia["id"],
            "is_essential": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["parent_id"] == moradia["id"]
    assert response.json()["type"] == "expense"
    assert response.json()["is_default"] is False


def test_category_hierarchy_cannot_contain_cycles(client):
    headers = auth_headers(client)
    parent_response = client.post(
        "/api/categories/",
        headers=headers,
        json={"name": "Veiculo", "type": "expense"},
    )
    child_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "Manutencao do veiculo",
            "type": "expense",
            "parent_id": parent_response.json()["id"],
        },
    )

    response = client.put(
        f"/api/categories/{parent_response.json()['id']}",
        headers=headers,
        json={"parent_id": child_response.json()["id"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Category hierarchy cannot contain cycles."


def test_deleting_parent_category_promotes_child_to_root(client):
    headers = auth_headers(client)
    parent_response = client.post(
        "/api/categories/",
        headers=headers,
        json={"name": "Assinaturas", "type": "expense"},
    )
    child_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "Streaming",
            "type": "expense",
            "parent_id": parent_response.json()["id"],
        },
    )

    delete_response = client.delete(
        f"/api/categories/{parent_response.json()['id']}",
        headers=headers,
    )
    categories_response = client.get("/api/categories/", headers=headers)
    child_after_delete = next(
        category
        for category in categories_response.json()
        if category["id"] == child_response.json()["id"]
    )

    assert delete_response.status_code == 204
    assert child_after_delete["parent_id"] is None


def test_authenticated_user_can_create_update_and_delete_category(client):
    headers = auth_headers(client)

    create_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "  Pet shop  ",
            "type": "expense",
            "is_essential": False,
        },
    )

    assert create_response.status_code == 201
    created_category = create_response.json()
    assert created_category["name"] == "Pet shop"
    assert created_category["type"] == "expense"
    assert created_category["is_default"] is False

    update_response = client.put(
        f"/api/categories/{created_category['id']}",
        headers=headers,
        json={
            "name": "Pets",
            "is_essential": True,
        },
    )

    assert update_response.status_code == 200
    updated_category = update_response.json()
    assert updated_category["name"] == "Pets"
    assert updated_category["is_essential"] is True

    delete_response = client.delete(
        f"/api/categories/{created_category['id']}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    categories_response = client.get("/api/categories/", headers=headers)
    names = {category["name"] for category in categories_response.json()}
    assert "Pets" not in names


@pytest.mark.parametrize("transaction_type", ["income", "expense"])
def test_deleting_category_reclassifies_transactions_as_unspecified(
    client,
    transaction_type,
):
    headers = auth_headers(
        client,
        name=f"Usuario {transaction_type}",
        email=f"{transaction_type}@example.com",
    )
    categories_response = client.get("/api/categories/", headers=headers)
    unspecified_category = next(
        category
        for category in categories_response.json()
        if category["name"] == "Nao especificado"
        and category["type"] == transaction_type
    )

    category_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": f"Categoria temporaria {transaction_type}",
            "type": transaction_type,
        },
    )
    category_id = category_response.json()["id"]

    transaction_response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": transaction_type,
            "amount": "50.00",
            "date": "2026-06-05",
            "category_id": category_id,
        },
    )
    transaction_id = transaction_response.json()["id"]

    delete_response = client.delete(
        f"/api/categories/{category_id}",
        headers=headers,
    )
    transaction_after_delete = client.get(
        f"/api/transactions/{transaction_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    assert transaction_after_delete.status_code == 200
    assert transaction_after_delete.json()["category_id"] == unspecified_category["id"]


def test_category_creation_rejects_duplicate_accessible_name(client):
    headers = auth_headers(client)

    duplicate_default_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "alimentacao",
            "type": "expense",
        },
    )

    assert duplicate_default_response.status_code == 409
    assert (
        duplicate_default_response.json()["detail"]
        == "A category with this name already exists for this type."
    )

    first_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "Viagens",
            "type": "expense",
        },
    )
    assert first_response.status_code == 201

    duplicate_user_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "viagens",
            "type": "expense",
        },
    )

    assert duplicate_user_response.status_code == 409


def test_default_categories_cannot_be_modified(client):
    headers = auth_headers(client)
    categories_response = client.get("/api/categories/", headers=headers)
    default_category = next(
        category
        for category in categories_response.json()
        if category["name"] == "Alimentacao"
    )

    update_response = client.put(
        f"/api/categories/{default_category['id']}",
        headers=headers,
        json={"name": "Mercado"},
    )
    delete_response = client.delete(
        f"/api/categories/{default_category['id']}",
        headers=headers,
    )

    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "Default categories cannot be modified."
    assert delete_response.status_code == 403
    assert delete_response.json()["detail"] == "Default categories cannot be modified."


def test_user_cannot_modify_another_users_category(client):
    first_headers = auth_headers(client, name="Usuario Um", email="usuario1@example.com")
    second_headers = auth_headers(client, name="Usuario Dois", email="usuario2@example.com")

    create_response = client.post(
        "/api/categories/",
        headers=first_headers,
        json={
            "name": "Assinaturas",
            "type": "expense",
        },
    )
    category_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/categories/{category_id}",
        headers=second_headers,
        json={"name": "Streaming"},
    )
    delete_response = client.delete(
        f"/api/categories/{category_id}",
        headers=second_headers,
    )

    assert update_response.status_code == 404
    assert delete_response.status_code == 404


def test_parent_category_must_have_same_type(client):
    headers = auth_headers(client)
    categories_response = client.get("/api/categories/", headers=headers)
    income_category = next(
        category
        for category in categories_response.json()
        if category["type"] == "income"
    )

    create_response = client.post(
        "/api/categories/",
        headers=headers,
        json={
            "name": "Mercado",
            "type": "expense",
            "parent_id": income_category["id"],
        },
    )

    assert create_response.status_code == 400
    assert create_response.json()["detail"] == "Parent category must have the same type as the category."
