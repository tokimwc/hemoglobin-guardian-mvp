from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field

class ImageQualityMetrics(BaseModel):
    """画像品質の評価指標"""
    is_blurry: bool
    brightness_score: Optional[float] = None
    has_proper_lighting: Optional[bool] = None
    has_detected_nail: Optional[bool] = None

class NailAnalysisResult(BaseModel):
    """Vision AIとGemini APIによる爪の解析結果"""
    risk_score: float
    confidence_score: float
    risk_level: str
    detected_colors: List[Dict[str, Any]]
    quality_metrics: ImageQualityMetrics
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: Optional[str] = None

    def to_dict(self) -> dict:
        """FirestoreのドキュメントとしてJSON化"""
        return {
            "risk_score": self.risk_score,
            "confidence_score": self.confidence_score,
            "risk_level": self.risk_level,
            "detected_colors": self.detected_colors,
            "quality_metrics": self.quality_metrics.dict(),
            "created_at": self.created_at,
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NailAnalysisResult':
        """Firestoreのドキュメントからインスタンスを生成"""
        quality_metrics = ImageQualityMetrics(**data.get("quality_metrics", {}))
        return cls(
            risk_score=data["risk_score"],
            confidence_score=data["confidence_score"],
            risk_level=data["risk_level"],
            detected_colors=data["detected_colors"],
            quality_metrics=quality_metrics,
            created_at=data.get("created_at"),
            user_id=data.get("user_id")
        )

class NutritionAdvice(BaseModel):
    """Gemini APIによる栄養アドバイス"""
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: List[str] = []

class AnalysisHistory(BaseModel):
    """解析履歴"""
    history_id: str
    user_id: str
    analysis_result: NailAnalysisResult
    nutrition_advice: Optional[NutritionAdvice] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    summary: str = "システムエラーが発生しました。"
    iron_rich_foods: List[str] = ["ひじき", "大豆", "小松菜"]
    meal_suggestions: List[str] = ["ひじきの煮物", "大豆と野菜の炒め物", "小松菜のおひたし"]
    lifestyle_tips: List[str] = ["バランスの取れた食事を心がけましょう。", "十分な睡眠を取りましょう。", "適度な運動をしましょう。"]
    warnings: List[str] = ["原因不明のエラーが発生しました。"]
    error_type: str = "SYSTEM_ERROR"

@dataclass
class UserProfile:
    """ユーザープロファイルを表すデータクラス"""
    user_id: str
    email: str
    created_at: str
    last_login: str
    analysis_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        return cls(**data) 