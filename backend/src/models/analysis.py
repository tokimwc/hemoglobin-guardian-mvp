from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel

@dataclass
class AnalysisResult:
    """解析結果を表すデータクラス"""
    risk_score: float
    risk_level: str
    advice: dict
    confidence_score: float
    warnings: List[str]
    quality_metrics: dict
    created_at: datetime = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """FirestoreのドキュメントとしてJSON化"""
        data = asdict(self)
        if self.created_at is None:
            data['created_at'] = datetime.utcnow()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisResult':
        """Firestoreのドキュメントからインスタンスを生成"""
        return cls(**data)

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

@dataclass
class AnalysisHistory:
    """解析履歴を表すデータクラス"""
    user_id: str
    results: List[AnalysisResult]
    last_updated: str
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'results': [result.to_dict() for result in self.results],
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisHistory':
        results = [AnalysisResult.from_dict(result) for result in data['results']]
        return cls(
            user_id=data['user_id'],
            results=results,
            last_updated=data['last_updated']
        )

class QualityMetrics(BaseModel):
    """画像品質の評価指標"""
    is_blurry: bool
    brightness_score: Optional[float] = None
    has_proper_lighting: Optional[bool] = None
    has_detected_nail: Optional[bool] = None

class AnalysisResult(BaseModel):
    """Vision AIとGemini APIによる解析結果"""
    risk_score: float
    risk_level: str
    advice: str
    confidence_score: float
    warnings: List[str]
    quality_metrics: QualityMetrics
    created_at: datetime

class AnalysisHistory(BaseModel):
    """解析履歴"""
    history_id: str
    user_id: str
    analysis_result: AnalysisResult
    created_at: datetime

class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    summary: str = "システムエラーが発生しました。"
    iron_rich_foods: List[str] = ["ひじき", "大豆", "小松菜"]
    meal_suggestions: List[str] = ["ひじきの煮物", "大豆と野菜の炒め物", "小松菜のおひたし"]
    lifestyle_tips: List[str] = ["バランスの取れた食事を心がけましょう。", "十分な睡眠を取りましょう。", "適度な運動をしましょう。"]
    warnings: List[str] = ["原因不明のエラーが発生しました。"]
    error_type: str = "SYSTEM_ERROR"

class NutritionAdvice(BaseModel):
    """Gemini APIによる栄養アドバイス"""
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: List[str] = []

class ImageQualityMetrics(BaseModel): # QualityMetricsからImageQualityMetricsにリネームされている場合は、こちらを修正
    is_blurry: bool
    brightness_score: Optional[float] = None
    has_proper_lighting: Optional[bool] = None
    has_detected_nail: Optional[bool] = None

class NailAnalysisResult(BaseModel): # AnalysisResultからNailAnalysisResultにリネームされている場合は、こちらを修正
    risk_score: float
    confidence_score: float
    detected_colors: List[Dict[str, Any]]
    quality_metrics: ImageQualityMetrics # QualityMetricsからImageQualityMetricsにリネームされている場合は、こちらを修正 