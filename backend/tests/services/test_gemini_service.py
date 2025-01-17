import pytest
from unittest.mock import Mock, patch
import json
import time
from src.services.gemini_service import GeminiService, NutritionAdvice, CacheKey, ErrorResponse

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
        assert isinstance(result, ErrorResponse)
        assert "システムエラー" in result.summary
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
        assert isinstance(result, ErrorResponse)
        assert "システムエラー" in result.summary
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

@pytest.mark.asyncio
async def test_cache_hit(gemini_service, mock_response):
    """キャッシュヒットのテスト"""
    with patch.object(gemini_service, '_call_gemini_api') as mock_call, \
         patch.object(gemini_service, '_create_error_response') as mock_error:
        mock_call.return_value = json.dumps(mock_response)
        
        # 1回目の呼び出し（キャッシュなし）
        result1 = await gemini_service.generate_advice(
            risk_level="LOW",
            confidence_score=0.9,
            warnings=[]
        )
        
        # 2回目の呼び出し（キャッシュヒット）
        result2 = await gemini_service.generate_advice(
            risk_level="LOW",
            confidence_score=0.9,
            warnings=[]
        )
        
        # 検証
        assert mock_call.call_count == 1  # APIは1回だけ呼ばれる
        assert isinstance(result1, NutritionAdvice)
        assert isinstance(result2, NutritionAdvice)
        assert result1.summary == result2.summary  # 内容が同じことを確認

@pytest.mark.asyncio
async def test_cache_expiration(gemini_service, mock_response):
    """キャッシュの有効期限テスト"""
    with patch.object(gemini_service, '_call_gemini_api') as mock_call:
        mock_call.return_value = json.dumps(mock_response)
        
        # キャッシュTTLを一時的に1秒に設定
        original_ttl = gemini_service._cache_ttl
        gemini_service._cache_ttl = 1
        
        # 1回目の呼び出し
        result1 = await gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=[]
        )
        
        # キャッシュの有効期限が切れるまで待機
        time.sleep(1.1)
        
        # 2回目の呼び出し
        result2 = await gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=[]
        )
        
        # TTLを元に戻す
        gemini_service._cache_ttl = original_ttl
        
        # 検証
        assert mock_call.call_count == 2  # APIが2回呼ばれる
        assert result2.cached == False  # 新しく生成されたことを確認

@pytest.mark.asyncio
async def test_cache_cleanup(gemini_service, mock_response):
    """キャッシュクリーンアップのテスト"""
    with patch.object(gemini_service, '_call_gemini_api') as mock_call, \
         patch.object(gemini_service, '_create_error_response') as mock_error:
        mock_call.return_value = json.dumps(mock_response)
        
        # キャッシュTTLとクリーンアップ間隔を一時的に設定
        original_ttl = gemini_service._cache_ttl
        original_cleanup_interval = gemini_service._last_cache_cleanup
        gemini_service._cache_ttl = 1
        
        # 複数のキャッシュエントリを作成
        test_cases = [
            ("LOW", ["警告1"]),
            ("MEDIUM", ["警告2"]),
            ("HIGH", ["警告3"])
        ]
        
        for risk_level, warnings in test_cases:
            await gemini_service.generate_advice(
                risk_level=risk_level,
                confidence_score=0.8,
                warnings=warnings
            )
        
        # キャッシュの有効期限が切れるまで待機
        time.sleep(1.1)
        
        # 最終クリーンアップ時刻を強制的に更新して、クリーンアップを実行
        gemini_service._last_cache_cleanup = 0
        gemini_service._cleanup_cache()
        
        # 設定を元に戻す
        gemini_service._cache_ttl = original_ttl
        gemini_service._last_cache_cleanup = original_cleanup_interval
        
        # 検証
        assert len(gemini_service._advice_cache) == 0  # キャッシュが空になっていることを確認

@pytest.mark.asyncio
async def test_cache_with_different_warnings(gemini_service, mock_response):
    """異なる警告でのキャッシュテスト"""
    with patch.object(gemini_service, '_call_gemini_api') as mock_call:
        mock_call.return_value = json.dumps(mock_response)
        
        # 異なる警告での呼び出し
        result1 = await gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=["警告1"]
        )
        
        result2 = await gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=["警告2"]
        )
        
        # 検証
        assert mock_call.call_count == 2  # 異なる警告なので2回APIが呼ばれる
        assert result1.warnings != result2.warnings

@pytest.mark.asyncio
async def test_cache_key_creation(gemini_service):
    """キャッシュキー生成のテスト"""
    # 同じ内容での複数回のキー生成
    key1 = CacheKey.create("LOW", ["警告1", "警告2"])
    key2 = CacheKey.create("LOW", ["警告2", "警告1"])  # 順序が異なる
    
    # 検証
    assert key1 == key2  # 警告の順序が異なっても同じキーになることを確認
    
    # 異なる内容でのキー生成
    key3 = CacheKey.create("MEDIUM", ["警告1"])
    assert key1 != key3  # リスクレベルが異なる場合は異なるキー 