from typing import Final, Literal, cast


EmotionType = Literal[
    "not_specified",
    "calma",
    "felicidade",
    "raiva",
    "frustracao",
    "empolgacao",
    "ansiedade",
    "estresse",
    "indiferenca",
    "satisfacao",
    "tedio",
]

DEFAULT_EMOTION: Final[EmotionType] = "not_specified"

VALID_EMOTIONS: Final[tuple[EmotionType, ...]] = (
    "not_specified",
    "calma",
    "felicidade",
    "raiva",
    "frustracao",
    "empolgacao",
    "ansiedade",
    "estresse",
    "indiferenca",
    "satisfacao",
    "tedio",
)

EMOTION_LABELS: Final[dict[EmotionType, str]] = {
    "not_specified": "Não especificada",
    "calma": "Calma",
    "felicidade": "Felicidade",
    "raiva": "Raiva",
    "frustracao": "Frustração",
    "empolgacao": "Empolgação",
    "ansiedade": "Ansiedade",
    "estresse": "Estresse",
    "indiferenca": "Indiferença",
    "satisfacao": "Satisfação",
    "tedio": "Tédio",
}


def normalize_emotion(value: str | None) -> EmotionType:
    if value is None:
        return DEFAULT_EMOTION

    normalized = value.strip().lower()
    if not normalized:
        return DEFAULT_EMOTION

    if normalized not in VALID_EMOTIONS:
        allowed = ", ".join(VALID_EMOTIONS)
        raise ValueError(f"Invalid emotion. Allowed values: {allowed}.")

    return cast(EmotionType, normalized)


def build_emotion_options() -> list[dict[str, str]]:
    return [
        {
            "value": emotion,
            "label": EMOTION_LABELS[emotion],
        }
        for emotion in VALID_EMOTIONS
    ]
