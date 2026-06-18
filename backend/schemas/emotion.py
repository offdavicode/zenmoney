from pydantic import BaseModel

from utils.emotion_rules import SelectableEmotionType


class EmotionOptionResponse(BaseModel):
    value: SelectableEmotionType
    label: str
