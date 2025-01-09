import pytest
from unittest.mock import Mock, patch
from src.services.gemini_service import GeminiService

@pytest.fixture
def gemini_service():
    with patch('google.cloud.aiplatform.gapic.PredictionServiceClient'):
        service = GeminiService()
        return service

def test_generate_advice(gemini_service):
    # 各リスクレベルでのアドバイス生成をテスト
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    
    for level in risk_levels:
        with patch.object(gemini_service, '_call_gemini_api') as mock_call:
            mock_call.return_value = f"鉄分を含む食事アドバイス: {level}"
            advice = gemini_service.generate_advice(level)
            
            # 検証
            assert isinstance(advice, str)
            assert len(advice) > 0
            assert "鉄分" in advice

def test_create_prompt(gemini_service):
    # 各リスクレベルでのプロンプト生成をテスト
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    
    for level in risk_levels:
        prompt = gemini_service._create_prompt(level)
        
        # 検証
        assert isinstance(prompt, str)
        assert "貧血予防の専門家" in prompt
        assert "鉄分" in prompt
        assert level in prompt

def test_invalid_risk_level(gemini_service):
    # 無効なリスクレベルの場合、MEDIUMのアドバイスが返されることをテスト
    with patch.object(gemini_service, '_call_gemini_api') as mock_call:
        mock_call.return_value = "鉄分を含む食事アドバイス: MEDIUM"
        advice = gemini_service.generate_advice("INVALID")
        
        # 検証
        assert isinstance(advice, str)
        assert len(advice) > 0
        assert "鉄分" in advice 