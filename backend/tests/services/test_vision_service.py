import pytest
from unittest.mock import Mock, patch
import asyncio
from src.services.vision_service import VisionService, ImageQualityMetrics, NailAnalysisResult

@pytest.fixture
def vision_service():
    return VisionService()

@pytest.fixture
def mock_image_content():
    return b"fake_image_content"

@pytest.fixture
def mock_vision_response():
    """Vision APIのモックレスポンスを生成"""
    mock_color = Mock()
    mock_color.color.red = 200
    mock_color.color.green = 150
    mock_color.color.blue = 150
    mock_color.score = 0.8

    mock_properties = Mock()
    mock_properties.image_properties_annotation.dominant_colors.colors = [mock_color]

    mock_object = Mock()
    mock_object.name = "Hand"
    mock_object.score = 0.9
    mock_objects = Mock()
    mock_objects.localized_object_annotations = [mock_object]

    mock_face = Mock()
    mock_faces = Mock()
    mock_faces.face_annotations = [mock_face]

    return mock_properties, mock_objects, mock_faces

@pytest.mark.asyncio
async def test_analyze_image_success(vision_service, mock_image_content, mock_vision_response):
    """画像解析の正常系テスト"""
    with patch.object(vision_service.client, 'image_properties') as mock_properties, \
         patch.object(vision_service.client, 'object_localization') as mock_objects, \
         patch.object(vision_service.client, 'face_detection') as mock_faces:
        
        mock_properties.return_value = mock_vision_response[0]
        mock_objects.return_value = mock_vision_response[1]
        mock_faces.return_value = mock_vision_response[2]

        result = await vision_service.analyze_image(mock_image_content)

        assert isinstance(result, NailAnalysisResult)
        assert 0 <= result.risk_score <= 1
        assert 0 <= result.confidence_score <= 1
        assert isinstance(result.quality_metrics, ImageQualityMetrics)
        assert len(result.detected_colors) > 0

def test_check_image_quality(vision_service, mock_vision_response):
    """画像品質チェックのテスト"""
    properties = mock_vision_response[0].image_properties_annotation
    quality_metrics = vision_service._check_image_quality(properties)

    assert isinstance(quality_metrics, ImageQualityMetrics)
    assert isinstance(quality_metrics.is_blurry, bool)
    assert 0 <= quality_metrics.brightness_score <= 1
    assert isinstance(quality_metrics.has_proper_lighting, bool)

def test_detect_nail_region(vision_service, mock_vision_response):
    """爪領域検出のテスト"""
    objects = mock_vision_response[1].localized_object_annotations
    has_nail = vision_service._detect_nail_region(objects)

    assert isinstance(has_nail, bool)
    assert has_nail  # "Hand"が検出されているため、Trueになるはず

def test_rgb_to_hsv_conversion(vision_service):
    """RGB→HSV変換のテスト"""
    # 赤色のテスト
    h, s, v = vision_service._rgb_to_hsv(255, 0, 0)
    assert h == 0
    assert s == 100
    assert v == 100

    # 白色のテスト
    h, s, v = vision_service._rgb_to_hsv(255, 255, 255)
    assert h == 0
    assert s == 0
    assert v == 100

    # ピンク色のテスト
    h, s, v = vision_service._rgb_to_hsv(255, 192, 203)
    assert 340 <= h <= 350
    assert 20 <= s <= 30
    assert 90 <= v <= 100

@pytest.mark.asyncio
async def test_analyze_image_error_handling(vision_service, mock_image_content):
    """エラーハンドリングのテスト"""
    with patch.object(vision_service.client, 'image_properties', side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc_info:
            await vision_service.analyze_image(mock_image_content)
        assert "API Error" in str(exc_info.value) 