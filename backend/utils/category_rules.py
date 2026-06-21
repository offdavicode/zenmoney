from typing import Final, Literal


CategoryType = Literal["income", "expense"]

VALID_CATEGORY_TYPES: Final[tuple[CategoryType, ...]] = ("income", "expense")
UNSPECIFIED_CATEGORY_NAME: Final[str] = "Não especificado"

DEFAULT_CATEGORIES_BY_TYPE: Final[dict[CategoryType, tuple[tuple[str, bool], ...]]] = {
    "income": (
        ("Salário", False),
        ("Aposentadoria", False),
        ("Pensão", False),
        ("Aluguel", False),
        ("Pró-labore", False),
        ("Comissão/Bônus", False),
        ("Freelance", False),
        ("Dividendos e juros", False),
        ("Venda de itens", False),
        ("Investimentos", False),
        ("Outros recebimentos", False),
        (UNSPECIFIED_CATEGORY_NAME, False),
    ),
    "expense": (
        ("Moradia", True),
        ("Contas Residenciais", True),
        ("Saúde", True),
        ("Educação", True),
        ("Alimentação", True),
        ("Transporte", True),
        ("Cuidados Pessoais", True),
        ("Hobbies", False),
        ("Roupas", False),
        ("Compras", False),
        ("Lazer", False),
        ("Investimentos", False),
        ("Dívidas", True),
        ("Reserva de emergência", False),
        ("Contas", True),
        ("Outros gastos", False),
        (UNSPECIFIED_CATEGORY_NAME, False),
    ),
}


def normalize_category_name(name: str) -> str:
    return " ".join(name.strip().split())


def is_valid_category_type(category_type: str) -> bool:
    return category_type in VALID_CATEGORY_TYPES


def build_default_category_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for category_type, categories in DEFAULT_CATEGORIES_BY_TYPE.items():
        for name, is_essential in categories:
            rows.append(
                {
                    "name": normalize_category_name(name),
                    "type": category_type,
                    "is_default": True,
                    "is_essential": is_essential,
                    "user_id": None,
                }
            )
    return rows
