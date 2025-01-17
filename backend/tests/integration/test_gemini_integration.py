import pytest
import os
from dotenv import load_dotenv
from src.services.gemini_service import GeminiService, NutritionAdvice

# 環境変数の読み込み
load_dotenv()

@pytest.fixture
def gemini_service():
    """実際のGemini APIを使用するサービスインスタンス"""
    return GeminiService()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_advice_low_risk(gemini_service):
    """低リスクケースでのアドバイス生成テスト"""
    result = await gemini_service.generate_advice(
        risk_level="LOW",
        confidence_score=0.9,
        warnings=[]
    )
    
    # 基本的な検証
    assert isinstance(result, NutritionAdvice)
    assert len(result.summary) > 0
    assert len(result.iron_rich_foods) > 0
    assert len(result.meal_suggestions) > 0
    assert len(result.lifestyle_tips) > 0
    
    # コンテンツの妥当性検証
    assert "予防" in result.summary.lower()
    assert any("レバー" in food or "ほうれん草" in food or "牡蠣" in food for food in result.iron_rich_foods)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_advice_high_risk(gemini_service):
    """高リスクケースでのアドバイス生成テスト"""
    result = await gemini_service.generate_advice(
        risk_level="HIGH",
        confidence_score=0.7,
        warnings=["画像が少し暗いです"]
    )
    
    # 基本的な検証
    assert isinstance(result, NutritionAdvice)
    assert len(result.summary) > 0
    assert len(result.iron_rich_foods) > 0
    assert len(result.meal_suggestions) > 0
    assert len(result.lifestyle_tips) > 0
    
    # コンテンツの妥当性検証
    assert "改善" in result.summary.lower() or "対策" in result.summary.lower()
    assert len(result.iron_rich_foods) >= 3  # より多くの食材を提案
    assert len(result.meal_suggestions) >= 2  # より多くのメニューを提案
    assert "画像が少し暗いです" in result.warnings

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_advice_with_warnings(gemini_service):
    """警告付きのアドバイス生成テスト"""
    warnings = [
        "画像が不鮮明です",
        "爪の検出精度が低いです"
    ]
    
    result = await gemini_service.generate_advice(
        risk_level="MEDIUM",
        confidence_score=0.5,
        warnings=warnings
    )
    
    # 基本的な検証
    assert isinstance(result, NutritionAdvice)
    assert len(result.summary) > 0
    
    # 警告の検証
    assert all(warning in result.warnings for warning in warnings)
    
    # 信頼度が低い場合の慎重な表現の検証
    assert "可能性" in result.summary or "かもしれません" in result.summary

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_advice_response_format(gemini_service):
    """レスポンスのフォーマット検証テスト"""
    result = await gemini_service.generate_advice(
        risk_level="MEDIUM",
        confidence_score=0.8,
        warnings=[]
    )
    
    # 各フィールドの型の検証
    assert isinstance(result.summary, str)
    assert isinstance(result.iron_rich_foods, list)
    assert isinstance(result.meal_suggestions, list)
    assert isinstance(result.lifestyle_tips, list)
    assert isinstance(result.warnings, list)
    
    # 文字列の長さの検証
    assert 20 <= len(result.summary) <= 200  # 要約は適度な長さ
    assert all(len(food) > 0 for food in result.iron_rich_foods)  # 空の食材名がない
    assert all(len(menu) > 0 for menu in result.meal_suggestions)  # 空のメニュー名がない
    assert all(len(tip) > 0 for tip in result.lifestyle_tips)  # 空のアドバイスがない 

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_advice_with_low_confidence(gemini_service):
    """非常に低い信頼度スコアでのアドバイス生成テスト"""
    result = await gemini_service.generate_advice(
        risk_level="MEDIUM",
        confidence_score=0.2,  # 非常に低い信頼度
        warnings=["画像の品質が非常に低いです"]
    )
    
    # 基本的な検証
    assert isinstance(result, NutritionAdvice)
    assert len(result.summary) > 0
    assert len(result.iron_rich_foods) > 0
    assert len(result.meal_suggestions) > 0
    assert len(result.lifestyle_tips) > 0
    
    # 低信頼度に関する警告の検証
    assert any("信頼度" in warning.lower() or "確実" not in result.summary.lower() for warning in result.warnings)
    assert "可能性" in result.summary or "かもしれません" in result.summary

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_advice_with_invalid_risk_level(gemini_service):
    """無効なリスクレベルでのアドバイス生成テスト"""
    result = await gemini_service.generate_advice(
        risk_level="INVALID",  # 無効なリスクレベル
        confidence_score=0.8,
        warnings=[]
    )
    
    # 基本的な検証
    assert isinstance(result, NutritionAdvice)
    assert len(result.summary) > 0
    
    # MEDIUMへのフォールバックを検証
    assert "可能性" in result.summary 