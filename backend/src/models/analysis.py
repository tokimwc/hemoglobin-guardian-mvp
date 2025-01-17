from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime
import json

@dataclass
class AnalysisResult:
    """解析結果を表すデータクラス"""
    user_id: str
    risk_level: str
    confidence_score: float
    image_quality_score: float
    warnings: List[str]
    nutrition_advice: dict
    created_at: str = None
    
    def to_dict(self) -> dict:
        """FirestoreのドキュメントとしてJSON化"""
        data = asdict(self)
        if self.created_at is None:
            data['created_at'] = datetime.utcnow().isoformat()
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