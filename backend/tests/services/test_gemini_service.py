import pytest
from unittest.mock import Mock, patch
import json
from src.services.gemini_service import GeminiService, NutritionAdvice

@pytest.fixture
def gemini_service():
    return GeminiService()

@pytest.fixture
def mock_gemini_response():
    return {
        "summary": "テスト用の栄養アドバイス要約",
        "iron_rich_foods": ["レバー", "ほうれん草"],
        "meal_suggestions": ["レバーの甘辛煮"],
        "lifestyle_tips": ["規則正しい食事を心がけましょう"]
    }

@pytest.mark.asyncio
async def test_generate_advice_success(gemini_service):
    """アドバイス生成の正常系テスト"""
    risk_level = "MEDIUM"
    confidence_score = 0.8
    warnings = ["テスト用警告"]

    result = await gemini_service.generate_advice(
        risk_level=risk_level,
        confidence_score=confidence_score,
        warnings=warnings
    )

    assert isinstance(result, NutritionAdvice)
    assert isinstance(result.summary, str)
    assert isinstance(result.iron_rich_foods, list)
    assert isinstance(result.meal_suggestions, list)
    assert isinstance(result.lifestyle_tips, list)
    assert isinstance(result.warnings, list)
    assert warnings[0] in result.warnings

@pytest.mark.asyncio
async def test_generate_advice_with_low_confidence(gemini_service):
    """低信頼度時のアドバイス生成テスト"""
    result = await gemini_service.generate_advice(
        risk_level="HIGH",
        confidence_score=0.3,
        warnings=["画像がブレています"]
    )

    assert isinstance(result, NutritionAdvice)
    assert "画像がブレています" in result.warnings

@pytest.mark.asyncio
async def test_generate_advice_error_handling(gemini_service):
    """エラー時のフォールバックテスト"""
    with patch.object(gemini_service, '_call_gemini_api', side_effect=Exception("API Error")):
        result = await gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=[]
        )

        assert isinstance(result, NutritionAdvice)
        assert "エラー" in result.summary.lower()
        assert len(result.warnings) > 0
        assert "API Error" in result.warnings[0]

def test_create_prompt(gemini_service):
    """プロンプト生成のテスト"""
    risk_level = "HIGH"
    confidence_score = 0.7
    warnings = ["テスト用警告"]

    prompt = gemini_service._create_prompt(risk_level, confidence_score, warnings)

    assert isinstance(prompt, str)
    assert "貧血予防の専門家" in prompt
    assert risk_level in prompt
    assert "70%" in prompt  # confidence_score
    assert warnings[0] in prompt

def test_format_response_success(gemini_service, mock_gemini_response):
    """レスポンス整形の正常系テスト"""
    response = json.dumps(mock_gemini_response)
    warnings = ["テスト用警告"]

    result = gemini_service._format_response(
        response=response,
        risk_level="LOW",
        warnings=warnings
    )

    assert isinstance(result, NutritionAdvice)
    assert result.summary == mock_gemini_response["summary"]
    assert result.iron_rich_foods == mock_gemini_response["iron_rich_foods"]
    assert result.meal_suggestions == mock_gemini_response["meal_suggestions"]
    assert result.lifestyle_tips == mock_gemini_response["lifestyle_tips"]
    assert warnings[0] in result.warnings

def test_format_response_invalid_json(gemini_service):
    """不正なJSONレスポンスのテスト"""
    invalid_response = "invalid json"
    warnings = []

    result = gemini_service._format_response(
        response=invalid_response,
        risk_level="MEDIUM",
        warnings=warnings
    )

    assert isinstance(result, NutritionAdvice)
    assert "申し訳ありません" in result.summary
    assert len(result.warnings) > 0
    assert "JSONDecodeError" in result.warnings[0]

def test_get_fallback_advice(gemini_service):
    """フォールバックアドバイスのテスト"""
    error = "テストエラー"
    result = gemini_service._get_fallback_advice("LOW", error)

    assert isinstance(result, NutritionAdvice)
    assert "申し訳ありません" in result.summary
    assert len(result.iron_rich_foods) > 0
    assert len(result.meal_suggestions) > 0
    assert len(result.lifestyle_tips) > 0
    assert error in result.warnings[0] 