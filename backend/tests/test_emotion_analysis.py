from datetime import date
from decimal import Decimal

import pytest

from models.transaction import Transaction


ANALYSIS_PATH = "/api/reports/emotion-spending-analysis"


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


def _create_expense(
    client,
    headers: dict[str, str],
    *,
    amount: str,
    emotion: str,
    category_id: int | None = None,
    transaction_date: str = "2026-06-10",
    description: str | None = None,
) -> dict:
    response = client.post(
        "/api/transactions/",
        headers=headers,
        json={
            "amount": amount,
            "emotion": emotion,
            "category_id": category_id,
            "date": transaction_date,
            "description": description,
            "type": "expense",
        },
    )
    assert response.status_code == 201
    return response.json()


def _create_many(
    client,
    headers: dict[str, str],
    *,
    count: int,
    amount: str,
    emotion: str,
    category_id: int | None = None,
    transaction_date: str = "2026-06-10",
) -> None:
    for _ in range(count):
        _create_expense(
            client,
            headers,
            amount=amount,
            emotion=emotion,
            category_id=category_id,
            transaction_date=transaction_date,
        )


def _create_legacy_not_specified_expenses(
    testing_session_local,
    *,
    user_id: int,
    count: int,
    amount: str,
    transaction_date: str = "2026-06-10",
) -> None:
    with testing_session_local() as db:
        for _ in range(count):
            db.add(
                Transaction(
                    user_id=user_id,
                    type="expense",
                    amount=Decimal(amount),
                    date=date.fromisoformat(transaction_date),
                    emotion="not_specified",
                )
            )
        db.commit()


def _emotion_item(data: dict, emotion: str) -> dict:
    return next(item for item in data["emotion_analysis"] if item["emotion"] == emotion)


def _category_trigger(data: dict, emotion: str, category_name: str) -> dict:
    return next(
        item
        for item in data["category_triggers"]
        if item["emotion"] == emotion and item["category_name"] == category_name
    )


def _emotion_details(data: dict, emotion: str) -> dict:
    return next(item for item in data["details_by_emotion"] if item["emotion"] == emotion)


def test_emotion_analysis_requires_authentication(client):
    response = client.get(f"{ANALYSIS_PATH}?month=2026-06")

    assert response.status_code == 401


def test_emotion_analysis_returns_empty_safe_result_without_expenses(client):
    headers = _register_and_login(client, "Ana RF09", "ana-rf09@example.com")

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["conclusions_enabled"] is True
    assert data["minimum_transactions"] == 5
    assert data["trigger_threshold_percentage"] == 20
    assert data["reference_emotions"] == [
        "calma",
        "felicidade",
        "indiferenca",
        "satisfacao",
    ]
    assert "empolgacao" in data["candidate_emotions"]
    assert data["overall_statistics"]["transaction_count"] == 0
    assert data["reference_statistics"]["transaction_count"] == 0
    assert data["category_distribution"] == []
    assert data["category_triggers"] == []
    assert all(item["is_trigger"] is False for item in data["emotion_analysis"])


def test_general_trigger_uses_weighted_reference_and_accepts_exactly_twenty_percent(client):
    headers = _register_and_login(client, "Bia RF09", "bia-rf09@example.com")
    _create_many(client, headers, count=4, amount="100.00", emotion="calma")
    _create_many(client, headers, count=1, amount="100.00", emotion="felicidade")
    _create_many(client, headers, count=5, amount="120.00", emotion="ansiedade")

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    assert response.status_code == 200
    data = response.json()
    ansiedade = _emotion_item(data, "ansiedade")
    assert data["reference_statistics"] == {
        "transaction_count": 5,
        "total_amount": "500.00",
        "average_amount": "100.00",
    }
    assert ansiedade["average_amount"] == "120.00"
    assert ansiedade["difference_percentage"] == 20.0
    assert ansiedade["sufficient_data"] is True
    assert ansiedade["is_trigger"] is True
    assert ansiedade["reason"] == "trigger"


def test_general_trigger_uses_exact_values_and_rejects_below_twenty_percent(client):
    headers = _register_and_login(client, "Caio RF09", "caio-rf09@example.com")
    _create_many(client, headers, count=5, amount="100.00", emotion="calma")
    _create_many(client, headers, count=5, amount="119.99", emotion="ansiedade")

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    ansiedade = _emotion_item(response.json(), "ansiedade")
    assert ansiedade["difference_percentage"] == 19.99
    assert ansiedade["sufficient_data"] is True
    assert ansiedade["is_trigger"] is False
    assert ansiedade["reason"] == "not_trigger"


def test_trigger_requires_five_candidate_and_five_reference_transactions(client):
    headers = _register_and_login(client, "Davi RF09", "davi-rf09@example.com")
    _create_many(client, headers, count=4, amount="200.00", emotion="ansiedade")
    _create_many(client, headers, count=5, amount="100.00", emotion="calma")
    first_response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    _create_many(client, headers, count=1, amount="200.00", emotion="ansiedade")
    second_headers = _register_and_login(client, "Eva RF09", "eva-rf09@example.com")
    _create_many(client, second_headers, count=5, amount="200.00", emotion="ansiedade")
    _create_many(client, second_headers, count=4, amount="100.00", emotion="calma")
    second_response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=second_headers)

    first_item = _emotion_item(first_response.json(), "ansiedade")
    second_item = _emotion_item(second_response.json(), "ansiedade")
    assert first_item["reason"] == "insufficient_candidate_data"
    assert second_item["reason"] == "insufficient_reference_data"
    assert first_item["is_trigger"] is False
    assert second_item["is_trigger"] is False


def test_conclusions_are_disabled_outside_a_single_month(client):
    headers = _register_and_login(client, "Fabi RF09", "fabi-rf09@example.com")
    _create_many(client, headers, count=5, amount="100.00", emotion="calma")
    _create_many(client, headers, count=5, amount="200.00", emotion="ansiedade")

    unbounded_response = client.get(ANALYSIS_PATH, headers=headers)
    cross_month_response = client.get(
        f"{ANALYSIS_PATH}?start_date=2026-05-01&end_date=2026-06-30",
        headers=headers,
    )

    assert unbounded_response.json()["conclusions_enabled"] is False
    assert cross_month_response.json()["conclusions_enabled"] is False
    assert _emotion_item(unbounded_response.json(), "ansiedade")["reason"] == (
        "period_not_single_month"
    )
    assert _emotion_item(cross_month_response.json(), "ansiedade")["is_trigger"] is False


def test_not_informed_is_displayed_but_excluded_from_reference_and_triggers(
    client,
    testing_session_local,
):
    headers = _register_and_login(client, "Gabi RF09", "gabi-rf09@example.com")
    user_id = client.get("/api/auth/me", headers=headers).json()["id"]
    _create_legacy_not_specified_expenses(
        testing_session_local,
        user_id=user_id,
        count=5,
        amount="1000.00",
    )
    _create_many(client, headers, count=5, amount="100.00", emotion="calma")
    _create_many(client, headers, count=5, amount="120.00", emotion="ansiedade")

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    data = response.json()
    not_informed = _emotion_item(data, "not_specified")
    assert not_informed["emotion_label"] == "Nao Informado"
    assert not_informed["role"] == "not_informed"
    assert not_informed["reason"] == "not_candidate"
    assert data["overall_statistics"]["transaction_count"] == 10
    assert data["overall_statistics"]["average_amount"] == "110.00"
    assert data["reference_statistics"]["average_amount"] == "100.00"
    assert _emotion_item(data, "ansiedade")["is_trigger"] is True
    not_informed_distribution = next(
        item
        for item in data["category_distribution"]
        if item["emotion"] == "not_specified"
    )
    assert not_informed_distribution["emotion_label"] == "Nao Informado"


def test_empolgacao_is_a_candidate_emotion_and_can_be_a_trigger(client):
    headers = _register_and_login(client, "Hugo RF09", "hugo-rf09@example.com")
    _create_many(client, headers, count=5, amount="100.00", emotion="satisfacao")
    _create_many(client, headers, count=5, amount="150.00", emotion="empolgacao")

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    item = _emotion_item(response.json(), "empolgacao")
    assert item["role"] == "candidate"
    assert item["is_trigger"] is True


def test_category_trigger_uses_reference_from_same_category(client):
    headers = _register_and_login(client, "Iara RF09", "iara-rf09@example.com")
    alimentacao = _get_category(client, headers, "Alimentação")
    lazer = _get_category(client, headers, "Lazer")
    _create_many(
        client,
        headers,
        count=5,
        amount="100.00",
        emotion="calma",
        category_id=alimentacao["id"],
    )
    _create_many(
        client,
        headers,
        count=5,
        amount="120.00",
        emotion="ansiedade",
        category_id=alimentacao["id"],
    )
    _create_many(
        client,
        headers,
        count=5,
        amount="1000.00",
        emotion="calma",
        category_id=lazer["id"],
    )

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    data = response.json()
    general = _emotion_item(data, "ansiedade")
    category = _category_trigger(data, "ansiedade", "Alimentação")
    assert general["is_trigger"] is False
    assert category["reference_average_amount"] == "100.00"
    assert category["difference_percentage"] == 20.0
    assert category["is_trigger"] is True


def test_category_trigger_requires_reference_in_same_category(client):
    headers = _register_and_login(client, "Jo RF09", "jo-rf09@example.com")
    alimentacao = _get_category(client, headers, "Alimentação")
    lazer = _get_category(client, headers, "Lazer")
    _create_many(
        client,
        headers,
        count=5,
        amount="200.00",
        emotion="ansiedade",
        category_id=alimentacao["id"],
    )
    _create_many(
        client,
        headers,
        count=5,
        amount="100.00",
        emotion="calma",
        category_id=lazer["id"],
    )

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    category = _category_trigger(response.json(), "ansiedade", "Alimentação")
    assert category["reference_transaction_count"] == 0
    assert category["reason"] == "insufficient_reference_data"
    assert category["is_trigger"] is False


def test_analysis_respects_user_month_and_category_filters(client):
    first_headers = _register_and_login(client, "Kai RF09", "kai-rf09@example.com")
    second_headers = _register_and_login(client, "Lia RF09", "lia-rf09@example.com")
    alimentacao = _get_category(client, first_headers, "Alimentação")
    lazer = _get_category(client, first_headers, "Lazer")
    second_alimentacao = _get_category(client, second_headers, "Alimentação")

    _create_many(
        client,
        first_headers,
        count=5,
        amount="100.00",
        emotion="calma",
        category_id=alimentacao["id"],
    )
    _create_many(
        client,
        first_headers,
        count=5,
        amount="120.00",
        emotion="ansiedade",
        category_id=alimentacao["id"],
    )
    _create_many(
        client,
        first_headers,
        count=5,
        amount="900.00",
        emotion="ansiedade",
        category_id=lazer["id"],
        transaction_date="2026-05-10",
    )
    _create_many(
        client,
        second_headers,
        count=5,
        amount="999.00",
        emotion="ansiedade",
        category_id=second_alimentacao["id"],
    )

    response = client.get(
        f"{ANALYSIS_PATH}?month=2026-06&category_id={alimentacao['id']}",
        headers=first_headers,
    )

    data = response.json()
    assert data["period"]["category_id"] == alimentacao["id"]
    assert _emotion_item(data, "ansiedade")["average_amount"] == "120.00"
    assert all(
        item["category_name"] == "Alimentação"
        for item in data["category_distribution"]
    )


def test_analysis_returns_top_categories_and_top_transactions_by_emotion(client):
    headers = _register_and_login(client, "Mia RF09", "mia-rf09@example.com")
    alimentacao = _get_category(client, headers, "Alimentação")
    lazer = _get_category(client, headers, "Lazer")
    first = _create_expense(
        client,
        headers,
        amount="300.00",
        emotion="ansiedade",
        category_id=lazer["id"],
        description="Maior gasto",
    )
    _create_expense(
        client,
        headers,
        amount="100.00",
        emotion="ansiedade",
        category_id=alimentacao["id"],
    )
    _create_expense(
        client,
        headers,
        amount="50.00",
        emotion="ansiedade",
        category_id=lazer["id"],
    )

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    details = _emotion_details(response.json(), "ansiedade")
    assert [item["category_name"] for item in details["top_categories"]] == [
        "Lazer",
        "Alimentação",
    ]
    assert details["top_categories"][0]["total_amount"] == "350.00"
    assert details["top_transactions"][0]["transaction_id"] == first["id"]
    assert details["top_transactions"][0]["description"] == "Maior gasto"


def test_analysis_limits_top_transactions_to_ten_items(client):
    headers = _register_and_login(client, "Nina RF09", "nina-rf09@example.com")
    for index in range(12):
        _create_expense(
            client,
            headers,
            amount=f"{index + 1}.00",
            emotion="tedio",
            description=f"Gasto {index + 1}",
        )

    response = client.get(f"{ANALYSIS_PATH}?month=2026-06", headers=headers)

    details = _emotion_details(response.json(), "tedio")
    assert len(details["top_transactions"]) == 10
    assert details["top_transactions"][0]["amount"] == "12.00"
    assert details["top_transactions"][-1]["amount"] == "3.00"


@pytest.mark.parametrize(
    ("query", "expected_status"),
    [
        ("month=2026-13", 400),
        ("month=2026-06&start_date=2026-06-01", 400),
        ("start_date=2026-06-20&end_date=2026-06-10", 400),
    ],
)
def test_analysis_rejects_invalid_or_ambiguous_periods(client, query, expected_status):
    headers = _register_and_login(client, f"Periodo {query[:3]}", f"{query[:3]}-rf09@example.com")

    response = client.get(f"{ANALYSIS_PATH}?{query}", headers=headers)

    assert response.status_code == expected_status
