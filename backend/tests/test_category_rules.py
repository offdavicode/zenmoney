from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.category import CategoryCreate, CategoryUpdate
from schemas.transaction import TransactionCreate
from utils.category_rules import (
    DEFAULT_CATEGORIES_BY_TYPE,
    UNSPECIFIED_CATEGORY_NAME,
    VALID_CATEGORY_TYPES,
    build_default_category_rows,
    is_valid_category_type,
)

REQUIRED_INCOME_CATEGORIES = {
    "Salario",
    "Aposentadoria",
    "Pensao",
    "Aluguel",
    "Pro-labore",
    "Comissao/bonus",
    "Freelance",
    "Dividendos e juros",
    "Venda de itens",
}

REQUIRED_EXPENSE_CATEGORIES = {
    "Moradia",
    "Contas Residenciais",
    "Saude",
    "Educacao",
    "Alimentacao",
    "Transporte",
    "Cuidados Pessoais",
    "Hobbies",
    "Roupas",
    "Compras",
    "Lazer",
    "Investimentos",
    "Dividas",
    "Reserva de emergencia",
}


def test_default_categories_cover_all_valid_types() -> None:
    assert set(DEFAULT_CATEGORIES_BY_TYPE) == set(VALID_CATEGORY_TYPES)

    rows = build_default_category_rows()

    assert rows
    assert {row["type"] for row in rows} == set(VALID_CATEGORY_TYPES)
    assert all(row["is_default"] is True for row in rows)
    assert all(row["user_id"] is None for row in rows)


def test_default_categories_include_all_rf03_categories() -> None:
    names_by_type = {
        category_type: {name for name, _ in categories}
        for category_type, categories in DEFAULT_CATEGORIES_BY_TYPE.items()
    }

    assert REQUIRED_INCOME_CATEGORIES <= names_by_type["income"]
    assert REQUIRED_EXPENSE_CATEGORIES <= names_by_type["expense"]


def test_each_category_type_has_an_unspecified_default() -> None:
    rows = build_default_category_rows()

    unspecified_types = {
        row["type"]
        for row in rows
        if row["name"] == UNSPECIFIED_CATEGORY_NAME
    }

    assert unspecified_types == set(VALID_CATEGORY_TYPES)


def test_category_name_is_normalized() -> None:
    created = CategoryCreate(name="  Alimentacao   fora  ", type="expense")
    updated = CategoryUpdate(name="  Cartao   de credito ")

    assert created.name == "Alimentacao fora"
    assert updated.name == "Cartao de credito"


def test_invalid_category_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        CategoryCreate(name="Transferencia", type="transfer")

    assert is_valid_category_type("income") is True
    assert is_valid_category_type("expense") is True
    assert is_valid_category_type("transfer") is False


def test_transaction_uses_same_category_type_rule() -> None:
    payload = TransactionCreate(
        type="income",
        amount=Decimal("100.00"),
        date=date(2026, 5, 29),
    )

    assert payload.type == "income"

    with pytest.raises(ValidationError):
        TransactionCreate(
            type="transfer",
            amount=Decimal("100.00"),
            date=date(2026, 5, 29),
        )
