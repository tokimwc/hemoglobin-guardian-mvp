import pytest
from unittest.mock import Mock, patch
import base64
import json
from src.services.vision_ai import analyze_image, calculate_risk_level
from src.models.analysis import AnalysisResult

@pytest.fixture
def sample_image_base64():
    with open('tests/data/test_images.json', 'r') as f:
        return json.load(f)['healthy_nail']

@pytest.fixture
def mock_vision_client():
    with patch('google.cloud.vision.ImageAnnotatorClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client

def test_analyze_image_success(mock_vision_client, sample_image_base64):
    # モックの設定
    mock_response = Mock()
    mock_response.image_properties_annotation.dominant_colors.colors = [
        Mock(color=Mock(red=230, green=200, blue=200), score=0.8),
        Mock(color=Mock(red=220, green=190, blue=190), score=0.2),
    ]
    mock_vision_client.image_properties.return_value = mock_response

    # テスト実行
    result = analyze_image(sample_image_base64)

    # 検証
    assert isinstance(result, AnalysisResult)
    assert result.risk_level in ['LOW', 'MEDIUM', 'HIGH']
    assert 0 <= result.confidence <= 1
    assert result.timestamp is not None

@pytest.mark.parametrize('color_values,expected_level', [
    ((230, 200, 200), 'LOW'),    # 健康的な色
    ((200, 150, 150), 'MEDIUM'), # やや貧血の可能性
    ((180, 120, 120), 'HIGH'),   # 貧血の可能性が高い
])
def test_calculate_risk_level(color_values, expected_level):
    red, green, blue = color_values
    mock_color = Mock(red=red, green=green, blue=blue)
    
    result = calculate_risk_level(mock_color)
    
    assert result == expected_level

def test_analyze_image_invalid_base64():
    with pytest.raises(ValueError) as exc_info:
        analyze_image('invalid base64 string')
    assert 'Invalid base64 encoding' in str(exc_info.value)

def test_analyze_image_service_error(mock_vision_client):
    mock_vision_client.image_properties.side_effect = Exception('API Error')
    
    with pytest.raises(Exception) as exc_info:
        analyze_image('SGVsbG8gV29ybGQ=')  # "Hello World" in base64
    assert 'API Error' in str(exc_info.value) 