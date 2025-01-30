import pytest
import json
import os
from pathlib import Path
from src.services.vision_service import VisionService
from src.services.gemini_service import GeminiService, ErrorResponse, NutritionAdvice
from src.models.analysis_result import AnalysisResult
import base64
import asyncio
from unittest.mock import MagicMock, AsyncMock
import time
from dotenv import load_dotenv
import logging

# ロガーの設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

TEST_IMAGE_PATH = Path(__file__).parent.parent / "test_data" / "test_image.jpg"

# モックレスポンスの定義
MOCK_NUTRITION_ADVICE_JSON = {
    "summary": "貧血のリスクは低めですが、予防的な対策をお勧めします。",
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

class MockGenerateResponse:
    """Gemini APIのレスポンスをモックするクラス"""
    def __init__(self, text):
        self.text = text
        
    def __await__(self):
        yield
        return self

@pytest.fixture
def vision_service(mocker):
    service = VisionService()
    mocker.patch.object(
        service,
        'analyze_image',
        return_value={
            'risk_level': 'MEDIUM',
            'confidence_score': 0.8,
            'color_properties': [
                {
                    'red': 255,
                    'green': 200,
                    'blue': 200,
                    'score': 0.8,
                    'pixel_fraction': 0.5
                }
            ]
        }
    )
    return service

@pytest.fixture
def gemini_service(mocker):
    """モック化されたGeminiServiceを提供するフィクスチャ"""
    service = GeminiService(
        project_id="test-project",
        location="us-central1"
    )
    
    mock_response = MockGenerateResponse(json.dumps(MOCK_NUTRITION_ADVICE_JSON))
    mocker.patch.object(
        service.model,
        'generate_content',
        return_value=mock_response
    )
    
    return service

@pytest.mark.asyncio
async def test_vision_gemini_integration(gemini_service):
    """Vision AIとGemini APIの統合テスト"""
    vision_result = {
        "risk_level": "low",
        "confidence_score": 0.85,
        "color_properties": {
            "dominant_color": "pink",
            "color_score": 0.75
        }
    }
    
    logger.debug(f"テスト入力: {vision_result}")
    response = await gemini_service.generate_advice(vision_result)
    logger.debug(f"テスト結果: {response}")
    
    assert isinstance(response, NutritionAdvice), f"予期せぬレスポンスタイプ: {type(response)}"
    assert response.summary, "サマリーが空です"
    assert len(response.iron_rich_foods) >= 3
    assert len(response.meal_suggestions) >= 2
    assert len(response.lifestyle_tips) >= 2

@pytest.mark.asyncio
async def test_error_handling(gemini_service):
    """エラーハンドリングのテスト"""
    # 無効な解析結果
    invalid_result = {
        "risk_level": None,
        "confidence_score": 0.0,
        "color_properties": {}
    }
    
    logger.debug(f"エラーテスト入力: {invalid_result}")
    response = await gemini_service.generate_advice(invalid_result)
    logger.debug(f"エラーテスト結果: {response}")
    
    # エラーレスポンスの検証
    assert isinstance(response, ErrorResponse)
    assert response.summary == "リスクレベルが見つかりません"
    assert "リスクレベルが含まれていません" in response.warnings[0]
    assert response.error_type == "VALIDATION_ERROR"
    
    # デフォルト値の検証
    assert len(response.iron_rich_foods) > 0
    assert len(response.meal_suggestions) > 0
    assert len(response.lifestyle_tips) > 0

@pytest.mark.asyncio
async def test_performance(gemini_service):
    """パフォーマンステスト"""
    vision_result = {
        "risk_level": "medium",
        "confidence_score": 0.75,
        "color_properties": {
            "dominant_color": "red",
            "color_score": 0.8
        }
    }

    logger.debug(f"パフォーマンステスト入力: {vision_result}")
    start_time = time.time()
    response = await gemini_service.generate_advice(vision_result)
    end_time = time.time()
    logger.debug(f"パフォーマンステスト結果: {response}")

    execution_time = end_time - start_time
    assert execution_time < 4.0, f"実行時間が長すぎます: {execution_time:.2f}秒"
    assert isinstance(response, NutritionAdvice), f"予期せぬレスポンスタイプ: {type(response)}"
    assert len(response.iron_rich_foods) >= 3
    assert len(response.meal_suggestions) >= 2
    assert len(response.lifestyle_tips) >= 2

@pytest.mark.asyncio
async def test_concurrent_requests(gemini_service):
    """並行リクエストのテスト"""
    vision_results = [
        {
            "risk_level": "low",
            "confidence_score": 0.9,
            "color_properties": {"dominant_color": "pink"}
        },
        {
            "risk_level": "medium",
            "confidence_score": 0.8,
            "color_properties": {"dominant_color": "red"}
        }
    ]

    logger.debug("並行リクエストテスト開始")
    
    # 並行でリクエストを実行
    tasks = []
    for idx, result in enumerate(vision_results):
        logger.debug(f"タスク {idx + 1} 作成: {result}")
        tasks.append(gemini_service.generate_advice(result))
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # レスポンスの検証
    for idx, response in enumerate(responses):
        logger.debug(f"レスポンス {idx + 1}: {response}")
        if isinstance(response, Exception):
            pytest.fail(f"リクエスト {idx + 1} でエラーが発生: {response}")
        
        assert not isinstance(response, ErrorResponse), \
            f"エラーレスポンスが返されました（リクエスト {idx + 1}）: {response}"
        assert isinstance(response, NutritionAdvice)
        assert len(response.iron_rich_foods) >= 3, \
            f"鉄分豊富な食品が不足しています（リクエスト {idx + 1}）"
        assert len(response.meal_suggestions) >= 3, \
            f"食事提案が不足しています（リクエスト {idx + 1}）"
 