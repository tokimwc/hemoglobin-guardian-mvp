from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class NutritionAdvice(BaseModel):
    """栄養アドバイスのモデルクラス"""
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: Optional[List[str]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": "貧血の可能性が低いですが、予防的な対策をお勧めします。",
                "iron_rich_foods": [
                    "ほうれん草",
                    "レバー",
                    "牛肉",
                    "あさり"
                ],
                "meal_suggestions": [
                    "朝食：ほうれん草のお浸しと納豆",
                    "昼食：レバーの生姜焼き定食",
                    "夕食：あさりの酒蒸し"
                ],
                "lifestyle_tips": [
                    "規則正しい食生活を心がけましょう",
                    "十分な睡眠をとりましょう",
                    "適度な運動を行いましょう"
                ],
                "warnings": [
                    "症状が続く場合は医師に相談してください"
                ]
            }
        }
    ) 