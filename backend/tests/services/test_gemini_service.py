import pytest
from unittest.mock import Mock, patch
import json
from src.services.gemini_service import GeminiService, NutritionAdvice

@pytest.fixture
def gemini_service():
    with patch('vertexai.init'), \
         patch('vertexai.language_models.TextGenerationModel.from_pretrained'):
        service = GeminiService()
        return service

@pytest.fixture
def mock_response():
    return {
        "summary": "貧血予防のための栄養バランスの良い食事を心がけましょう。",
        "iron_rich_foods": ["レバー", "ほうれん草", "牡蠣", "枝豆"],
        "meal_suggestions": ["レバーの生姜焼き", "ほうれん草と豆腐の炒め物"],
        "lifestyle_tips": ["規則正しい食事を心がける", "ビタミンCを含む食品と一緒に摂取する"]
    }

@pytest.mark.asyncio
async def test_generate_advice_success(gemini_service, mock_response):
    """正常系: アドバイス生成が成功するケース"""
    # モックの設定
    with patch.object(gemini_service, '_call_gemini_api') as mock_call:
        mock_call.return_value = json.dumps(mock_response)
        
        # テスト実行
        result = await gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=["画像が少し暗いです"]
        )
        
        # 検証
        assert isinstance(result, NutritionAdvice)
        assert result.summary == mock_response["summary"]
        assert result.iron_rich_foods == mock_response["iron_rich_foods"]
        assert result.meal_suggestions == mock_response["meal_suggestions"]
        assert result.lifestyle_tips == mock_response["lifestyle_tips"]
        assert "画像が少し暗いです" in result.warnings

@pytest.mark.asyncio
async def test_generate_advice_api_error(gemini_service):
    """異常系: API呼び出しが失敗するケース"""
    # モックの設定
    with patch.object(gemini_service, '_call_gemini_api') as mock_call:
        mock_call.side_effect = Exception("API error")
        
        # テスト実行
        result = await gemini_service.generate_advice(
            risk_level="HIGH",
            confidence_score=0.6,
            warnings=[]
        )
        
        # 検証
        assert isinstance(result, NutritionAdvice)
        assert "申し訳ありません" in result.summary
        assert len(result.iron_rich_foods) > 0
        assert len(result.meal_suggestions) > 0
        assert len(result.lifestyle_tips) > 0
        assert any("API error" in warning for warning in result.warnings)

@pytest.mark.asyncio
async def test_generate_advice_invalid_json(gemini_service):
    """異常系: 不正なJSONレスポンスを受け取るケース"""
    # モックの設定
    with patch.object(gemini_service, '_call_gemini_api') as mock_call:
        mock_call.return_value = "invalid json"
        
        # テスト実行
        result = await gemini_service.generate_advice(
            risk_level="LOW",
            confidence_score=0.9,
            warnings=[]
        )
        
        # 検証
        assert isinstance(result, NutritionAdvice)
        assert "申し訳ありません" in result.summary
        assert any("JSONDecodeError" in warning for warning in result.warnings)

def test_create_prompt(gemini_service):
    """プロンプト生成のテスト"""
    # テスト実行
    prompt = gemini_service._create_prompt(
        risk_level="HIGH",
        confidence_score=0.7,
        warnings=["画像が不鮮明です"]
    )
    
    # 検証
    assert "貧血予防の専門家です" in prompt
    assert "貧血リスクは高めです" in prompt
    assert "70%" in prompt
    assert "画像が不鮮明です" in prompt

@pytest.mark.parametrize("risk_level", ["LOW", "MEDIUM", "HIGH", "UNKNOWN"])
def test_create_prompt_risk_levels(gemini_service, risk_level):
    """異なるリスクレベルでのプロンプト生成テスト"""
    # テスト実行
    prompt = gemini_service._create_prompt(
        risk_level=risk_level,
        confidence_score=0.8,
        warnings=[]
    )
    
    # 検証
    if risk_level in ["LOW", "MEDIUM", "HIGH"]:
        assert risk_level in prompt.upper()
    else:
        assert "MEDIUM" in prompt.upper()  # 不明なリスクレベルの場合のフォールバック 