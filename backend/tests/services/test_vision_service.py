import pytest
from unittest.mock import Mock, patch
import numpy as np
from src.services.vision_service import VisionService

@pytest.fixture
def vision_service():
    with patch('google.cloud.vision.ImageAnnotatorClient'):
        service = VisionService()
        return service

@pytest.fixture
def mock_vision_response():
    mock_color = Mock()
    mock_color.color.red = 255
    mock_color.color.green = 192
    mock_color.color.blue = 203
    mock_color.score = 0.8
    
    mock_properties = Mock()
    mock_properties.dominant_colors.colors = [mock_color]
    
    return mock_properties

def test_analyze_image(vision_service, mock_vision_response):
    with patch.object(vision_service.client, 'image_properties') as mock_properties:
        mock_properties.return_value.image_properties_annotation = mock_vision_response
        
        result = vision_service.analyze_image(b"dummy_image_data")
        
        assert isinstance(result, float)
        assert 0 <= result <= 1
        mock_properties.assert_called_once()

def test_calculate_risk_score(vision_service, mock_vision_response):
    score = vision_service._calculate_risk_score(mock_vision_response)
    
    assert isinstance(score, float)
    assert 0 <= score <= 1 