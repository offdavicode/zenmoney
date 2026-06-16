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
        "/api/reports/visual",
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


def test_visual_report_returns_empty_sections_without_expenses(client):
    token = _register_and_login(client, "Wesley Moraes", "wesley@example.com")
    headers = _auth_headers(token)

    response = client.get("/api/reports/visual", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_expense"] == "0.00"
    assert data["category_distribution"]["pie_items"] == []
    assert data["category_distribution"]["bar_items"] == []
    assert data["category_distribution"]["textual_items"] == []
    assert data["emotion_distribution"]["pie_items"] == []


def test_report_month_filter_is_applied_to_summary_and_visual_report(client):
    token = _register_and_login(client, "Yara Dias", "yara@example.com")
    headers = _auth_headers(token)

    for amount, transaction_date in (
        ("100.00", "2026-05-31"),
        ("200.00", "2026-06-01"),
        ("300.00", "2026-06-30"),
        ("400.00", "2026-07-01"),
    ):
        client.post(
            "/api/transactions/",
            headers=headers,
            json={
                "type": "expense",
                "amount": amount,
                "date": transaction_date,
                "emotion": "calma",
            },
        )

    summary_response = client.get("/api/reports/summary?month=2026-06", headers=headers)
    visual_response = client.get("/api/reports/visual?month=2026-06", headers=headers)

    assert summary_response.status_code == 200
    assert summary_response.json()["expense_count"] == 2
    assert summary_response.json()["total_expense"] == "500.00"

    assert visual_response.status_code == 200
    visual_data = visual_response.json()
    assert visual_data["period"]["start_date"] == "2026-06-01"
    assert visual_data["period"]["end_date"] == "2026-06-30"
    assert visual_data["total_expense"] == "500.00"


def test_report_custom_period_includes_both_boundary_dates(client):
    token = _register_and_login(client, "Amanda Reis", "amanda@example.com")
    headers = _auth_headers(token)

    for transaction_date in ("2026-06-09", "2026-06-10", "2026-06-20", "2026-06-21"):
        client.post(
            "/api/transactions/",
            headers=headers,
            json={
                "type": "expense",
                "amount": "10.00",
                "date": transaction_date,
                "emotion": "calma",
            },
        )

    response = client.get(
        "/api/reports/summary?start_date=2026-06-10&end_date=2026-06-20",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["expense_count"] == 2
    assert response.json()["total_expense"] == "20.00"


def test_report_accepts_maximum_supported_end_date(client):
    token = _register_and_login(client, "Alice Vale", "alice@example.com")
    headers = _auth_headers(token)
    client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "type": "expense",
            "amount": "10.00",
            "date": "9999-12-31",
            "emotion": "calma",
        },
    )

    response = client.get("/api/reports/summary?end_date=9999-12-31", headers=headers)

    assert response.status_code == 200
    assert response.json()["total_expense"] == "10.00"


@pytest.mark.parametrize(
    ("query", "expected_detail"),
    [
        (
            "month=2026-06&start_date=2026-06-01",
            "Use either month or start_date/end_date, not both.",
        ),
        (
            "start_date=2026-06-20&end_date=2026-06-10",
            "start_date must be before or equal to end_date.",
        ),
        (
            "month=2026-13",
            "Month must use YYYY-MM format.",
        ),
    ],
)
def test_report_rejects_ambiguous_or_invalid_periods(client, query, expected_detail):
    token = _register_and_login(client, "Bruno Nunes", f"bruno-{query[:4]}@example.com")
    headers = _auth_headers(token)

    response = client.get(f"/api/reports/visual?{query}", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == expected_detail


def test_report_category_filter_only_includes_selected_accessible_category(client):
    first_token = _register_and_login(client, "Carla Melo", "carla@example.com")
    second_token = _register_and_login(client, "Diego Vaz", "diego@example.com")
    first_headers = _auth_headers(first_token)
    second_headers = _auth_headers(second_token)
    alimentacao = _get_category_by_name(client, first_headers, "Alimentacao")
    lazer = _get_category_by_name(client, first_headers, "Lazer")
    private_category_id = _create_expense_category(client, second_headers, "Privada")

    for category_id, amount, emotion in (
        (alimentacao["id"], "100.00", "calma"),
        (lazer["id"], "300.00", "ansiedade"),
    ):
        client.post(
            "/api/transactions/",
            headers=first_headers,
            json={
                "category_id": category_id,
                "type": "expense",
                "amount": amount,
                "date": "2026-06-06",
                "emotion": emotion,
            },
        )

    filtered_response = client.get(
        f"/api/reports/visual?category_id={alimentacao['id']}",
        headers=first_headers,
    )
    inaccessible_response = client.get(
        f"/api/reports/visual?category_id={private_category_id}",
        headers=first_headers,
    )

    assert filtered_response.status_code == 200
    filtered_data = filtered_response.json()
    assert filtered_data["total_expense"] == "100.00"
    assert [item["label"] for item in filtered_data["category_distribution"]["pie_items"]] == [
        "Alimentacao"
    ]
    assert [item["key"] for item in filtered_data["emotion_distribution"]["pie_items"]] == [
        "calma"
    ]

    assert inaccessible_response.status_code == 404
    assert inaccessible_response.json()["detail"] == "Expense category not found."


def test_emotion_insight_requires_five_specified_expenses_in_period(client):
    token = _register_and_login(client, "Eduarda Lima", "eduarda@example.com")
    headers = _auth_headers(token)

    for emotion, count in (("ansiedade", 4), ("felicidade", 5), ("not_specified", 5)):
        for _ in range(count):
            client.post(
                "/api/transactions/",
                headers=headers,
                json={
                    "type": "expense",
                    "amount": "10.00",
                    "date": "2026-06-06",
                    "emotion": emotion,
                },
            )

    response = client.get("/api/reports/by-emotion?month=2026-06", headers=headers)
    unbounded_response = client.get("/api/reports/by-emotion", headers=headers)

    assert response.status_code == 200
    report = response.json()
    ansiedade = _find_emotion_item(report, "ansiedade")
    felicidade = _find_emotion_item(report, "felicidade")
    not_specified = _find_emotion_item(report, "not_specified")
    assert ansiedade["insight_eligible"] is False
    assert felicidade["insight_eligible"] is True
    assert felicidade["average_amount"] == "10.00"
    assert not_specified["insight_eligible"] is False
    assert (
        _find_emotion_item(unbounded_response.json(), "felicidade")["insight_eligible"]
        is False
    )


def test_visual_report_groups_tiny_items_but_keeps_them_in_text(client):
    token = _register_and_login(client, "Fabio Costa", "fabio@example.com")
    headers = _auth_headers(token)
    large_category_id = _create_expense_category(client, headers, "Gasto principal")
    tiny_category_id = _create_expense_category(client, headers, "Gasto infimo")

    for category_id, amount, emotion in (
        (large_category_id, "999.00", "calma"),
        (tiny_category_id, "1.00", "tedio"),
    ):
        client.post(
            "/api/transactions/",
            headers=headers,
            json={
                "category_id": category_id,
                "type": "expense",
                "amount": amount,
                "date": "2026-06-06",
                "emotion": emotion,
            },
        )

    response = client.get("/api/reports/visual?month=2026-06", headers=headers)

    assert response.status_code == 200
    category_section = response.json()["category_distribution"]
    assert [item["label"] for item in category_section["pie_items"]] == [
        "Gasto principal",
        "Outros",
    ]
    assert category_section["pie_items"][1]["is_aggregated"] is True
    assert category_section["pie_items"][1]["total_amount"] == "1.00"
    assert [item["label"] for item in category_section["textual_items"]] == ["Gasto infimo"]


def test_visual_report_keeps_item_at_exactly_one_percent_in_charts(client):
    token = _register_and_login(client, "Helena Paz", "helena@example.com")
    headers = _auth_headers(token)
    large_category_id = _create_expense_category(client, headers, "Principal")
    threshold_category_id = _create_expense_category(client, headers, "Exatamente um por cento")

    for category_id, amount in (
        (large_category_id, "99.00"),
        (threshold_category_id, "1.00"),
    ):
        client.post(
            "/api/transactions/",
            headers=headers,
            json={
                "category_id": category_id,
                "type": "expense",
                "amount": amount,
                "date": "2026-06-06",
                "emotion": "calma",
            },
        )

    response = client.get("/api/reports/visual?month=2026-06", headers=headers)

    assert response.status_code == 200
    category_section = response.json()["category_distribution"]
    assert [item["label"] for item in category_section["pie_items"]] == [
        "Principal",
        "Exatamente um por cento",
    ]
    assert category_section["textual_items"] == []


def test_visual_report_limits_chart_to_ten_items_and_groups_the_remainder(client):
    token = _register_and_login(client, "Gabriela Luz", "gabriela@example.com")
    headers = _auth_headers(token)

    for index in range(11):
        category_id = _create_expense_category(client, headers, f"Categoria {index:02d}")
        client.post(
            "/api/transactions/",
            headers=headers,
            json={
                "category_id": category_id,
                "type": "expense",
                "amount": "10.00",
                "date": "2026-06-06",
                "emotion": "calma",
            },
        )

    response = client.get("/api/reports/visual?month=2026-06", headers=headers)

    assert response.status_code == 200
    category_section = response.json()["category_distribution"]
    assert len(category_section["pie_items"]) == 10
    assert category_section["pie_items"][-1]["label"] == "Outros"
    assert category_section["pie_items"][-1]["transaction_count"] == 2
    assert len(category_section["bar_items"]) == 10
    assert all(item["label"] != "Outros" for item in category_section["bar_items"])
    assert len(category_section["textual_items"]) == 1
