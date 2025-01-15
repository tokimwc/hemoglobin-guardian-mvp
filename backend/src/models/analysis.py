from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AnalysisResult(BaseModel):
    """画像解析結果のレスポンスモデル"""
    risk_score: float
    risk_level: str
    advice: str
    created_at: datetime = datetime.now()
    image_url: Optional[str] = None

class AnalysisHistory(BaseModel):
    """解析履歴のレスポンスモデル"""
    history_id: str
    user_id: str
    analysis_result: AnalysisResult
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 