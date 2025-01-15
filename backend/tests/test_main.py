import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import io
from main import app
from src.models.analysis import AnalysisResult, ImageQualityMetrics, NutritionAdvice
from src.services.vision_service import NailAnalysisResult

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_image():
    return io.BytesIO(b"fake_image_content")

@pytest.fixture
def mock_vision_result():
    return NailAnalysisResult(
        risk_score=0.5,
        quality_metrics=ImageQualityMetrics(
            is_blurry=False,
            brightness_score=0.7,
            has_proper_lighting=True,
            has_detected_nail=True
        ),
        detected_colors=[{
            'hsv': (0, 50, 80),
            'score': 0.8,
            'rgb': (200, 150, 150)
        }],
        confidence_score=0.8
    )

@pytest.fixture
def mock_nutrition_advice():
    return NutritionAdvice(
        summary="テスト用アドバイス",
        iron_rich_foods=["レバー", "ほうれん草"],
        meal_suggestions=["レバーの甘辛煮"],
        lifestyle_tips=["規則正しい食事を心がけましょう"],
        warnings=[]
    )

def test_health_check(test_client):
    """ヘルスチェックエンドポイントのテスト"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "version" in response.json()

@pytest.mark.asyncio
async def test_analyze_image_success(test_client, mock_image, mock_vision_result, mock_nutrition_advice):
    """画像解析エンドポイントの正常系テスト"""
    with patch('src.services.vision_service.VisionService.analyze_image') as mock_vision, \
         patch('src.services.gemini_service.GeminiService.generate_advice') as mock_gemini:
        
        mock_vision.return_value = mock_vision_result
        mock_gemini.return_value = mock_nutrition_advice

        files = {"file": ("test.jpg", mock_image, "image/jpeg")}
        response = test_client.post("/analyze", files=files)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["risk_score"], float)
        assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        assert isinstance(data["confidence_score"], float)
        assert "quality_metrics" in data
        assert "advice" in data
        assert isinstance(data["warnings"], list)

@pytest.mark.asyncio
async def test_analyze_image_with_user_id(test_client, mock_image, mock_vision_result, mock_nutrition_advice):
    """ユーザーID付きの画像解析テスト"""
    with patch('src.services.vision_service.VisionService.analyze_image') as mock_vision, \
         patch('src.services.gemini_service.GeminiService.generate_advice') as mock_gemini, \
         patch('src.services.firestore_service.FirestoreService.save_analysis_result') as mock_save:
        
        mock_vision.return_value = mock_vision_result
        mock_gemini.return_value = mock_nutrition_advice
        mock_save.return_value = None

        files = {"file": ("test.jpg", mock_image, "image/jpeg")}
        response = test_client.post("/analyze", files=files, params={"user_id": "test_user"})

        assert response.status_code == 200
        mock_save.assert_called_once()

def test_analyze_image_no_file(test_client):
    """ファイルなしでのリクエストテスト"""
    response = test_client.post("/analyze")
    assert response.status_code == 422  # Validation Error

def test_analyze_image_invalid_file(test_client):
    """不正なファイルでのテスト"""
    files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
    response = test_client.post("/analyze", files=files)
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_get_history_success(test_client):
    """履歴取得エンドポイントの正常系テスト"""
    mock_history = [
        AnalysisHistory(
            history_id="test_id",
            user_id="test_user",
            analysis_result=AnalysisResult(
                risk_score=0.5,
                risk_level="MEDIUM",
                confidence_score=0.8,
                warnings=[],
                quality_metrics=ImageQualityMetrics(
                    is_blurry=False,
                    brightness_score=0.7,
                    has_proper_lighting=True,
                    has_detected_nail=True
                ),
                advice=mock_nutrition_advice
            )
        )
    ]

    with patch('src.services.firestore_service.FirestoreService.get_user_history') as mock_get:
        mock_get.return_value = mock_history
        response = test_client.get("/history/test_user")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["user_id"] == "test_user"

def test_get_history_invalid_user(test_client):
    """存在しないユーザーの履歴取得テスト"""
    with patch('src.services.firestore_service.FirestoreService.get_user_history', side_effect=Exception("User not found")):
        response = test_client.get("/history/invalid_user")
        assert response.status_code == 500
        assert "エラー" in response.json()["detail"] 