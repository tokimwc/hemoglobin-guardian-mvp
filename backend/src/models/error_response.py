from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional, List

class ErrorResponse(BaseModel):
    """エラーレスポンスのモデルクラス"""
    summary: str
    warnings: List[str]
    iron_rich_foods: Optional[List[str]] = None
    meal_suggestions: Optional[List[str]] = None
    lifestyle_tips: Optional[List[str]] = None
    error_type: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": "エラーが発生しました",
                "warnings": ["詳細なエラーメッセージ"],
                "iron_rich_foods": ["ほうれん草", "レバー", "牛肉"],
                "meal_suggestions": ["鉄分豊富な食事を心がけましょう"],
                "lifestyle_tips": ["十分な睡眠をとりましょう"],
                "error_type": "VALIDATION_ERROR"
            }
        }
    ) 