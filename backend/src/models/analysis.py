from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ImageQualityMetrics(BaseModel):
    """画像品質メトリクス"""
    is_blurry: bool
    brightness_score: float
    has_proper_lighting: bool
    has_detected_nail: bool

class NutritionAdvice(BaseModel):
    """栄養アドバイスモデル"""
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]

class AnalysisResult(BaseModel):
    """画像解析結果のレスポンスモデル"""
    risk_score: float
    risk_level: str
    confidence_score: float
    warnings: List[str]
    quality_metrics: ImageQualityMetrics
    advice: NutritionAdvice
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