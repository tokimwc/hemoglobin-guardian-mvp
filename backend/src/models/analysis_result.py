from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Optional
from datetime import datetime

class AnalysisResult(BaseModel):
    """画像解析結果のモデルクラス"""
    id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = datetime.now()
    risk_level: str
    risk_score: float
    advice_text: str
    image_url: Optional[str] = None
    vision_ai_results: Dict
    gemini_results: Optional[Dict] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    ) 