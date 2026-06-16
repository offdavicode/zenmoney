from pydantic import BaseModel

from utils.emotion_rules import EmotionType


class EmotionOptionResponse(BaseModel):
    value: EmotionType
    label: str
