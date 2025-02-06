from typing import Dict, Any, Optional
from datetime import datetime
from src.models.analysis import AnalysisResult, QualityMetrics

class MockVisionService:
    """Vision AIサービスのモック"""
    async def analyze_image_async(self, image_content: bytes) -> AnalysisResult:
        """
        VisionServiceのモック.
        常に固定のAnalysisResultを返す.
        """
        quality_metrics = QualityMetrics(
            is_blurry=False,
            brightness_score=0.8,
            has_proper_lighting=True,
            has_detected_nail=True
        )
        return AnalysisResult(
            risk_score=0.2,
            risk_level="LOW",
            advice="モックのアドバイス",
            confidence_score=0.9,
            warnings=[],
            quality_metrics=quality_metrics,
            created_at=datetime.now()
        )

class MockGeminiService:
    """Gemini APIサービスのモック"""
    def __init__(self, *args, **kwargs):
        pass

    async def generate_advice(self, image_content):
        return "Mock advice for low risk"

class MockFirestoreService:
    """Firestoreサービスのモック"""
    def __init__(self):
        self.storage = {}

    async def save_analysis_result(self, user_id: str, analysis_result: Dict[str, Any]):
        if user_id not in self.storage:
            self.storage[user_id] = []
        self.storage[user_id].append({
            **analysis_result,
            "created_at": datetime.now()
        })
        return True

    async def get_user_history(self, user_id: str, limit: Optional[int] = 10) -> list:
        if user_id not in self.storage:
            return []
        return sorted(
            self.storage[user_id],
            key=lambda x: x["created_at"],
            reverse=True
        )[:limit] 