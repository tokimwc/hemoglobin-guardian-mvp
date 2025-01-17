import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
from ...src.routers.analysis import router
from ...src.models.analysis import AnalysisResult, AnalysisHistory
from ...src.models.auth import UserData

app = FastAPI()
app.include_router(router)
client = TestClient(app)

# テスト用のモックデータ
MOCK_USER = UserData(
    user_id="test_user_123",
    email="test@example.com",
    analysis_count=5
)

VALID_ANALYSIS_RESULT = {
    "user_id": "test_user_123",
    "risk_level": "MEDIUM",
    "confidence_score": 0.85,
    "image_quality_score": 0.9,
    "warnings": ["画像が少し暗めです"],
    "nutrition_advice": {
        "summary": "貧血の可能性があるため、積極的な鉄分摂取をお勧めします。",
        "iron_rich_foods": ["レバー", "ほうれん草", "牡蠣"],
        "meal_suggestions": ["レバーの生姜焼き", "ほうれん草の胡麻和え"],
        "lifestyle_tips": ["規則正しい食事を心がけましょう"]
    },
    "created_at": datetime.utcnow().isoformat()
}

@pytest.fixture
def mock_firebase_service(mocker):
    """FirebaseServiceのモック"""
    mock_service = mocker.patch("src.services.firebase_service.FirebaseService")
    mock_service.return_value.save_analysis_result.return_value = "mock_doc_id_123"
    mock_service.return_value.get_analysis_history.return_value = AnalysisHistory(
        user_id=MOCK_USER.user_id,
        results=[AnalysisResult(**VALID_ANALYSIS_RESULT)],
        last_updated=datetime.utcnow().isoformat()
    )
    return mock_service

@pytest.fixture
def mock_auth(mocker):
    """認証のモック"""
    mocker.patch(
        "src.routers.auth.get_current_user",
        return_value=MOCK_USER
    )

def test_save_analysis_result_success(mock_firebase_service, mock_auth):
    """解析結果の保存（正常系）"""
    response = client.post("/analysis/save", json=VALID_ANALYSIS_RESULT)
    assert response.status_code == 201
    assert response.json()["message"] == "解析結果を保存しました"
    assert "result_id" in response.json()

def test_save_analysis_result_invalid_user(mock_firebase_service, mock_auth):
    """解析結果の保存（異常系：不正なユーザー）"""
    invalid_result = VALID_ANALYSIS_RESULT.copy()
    invalid_result["user_id"] = "different_user_456"
    
    response = client.post("/analysis/save", json=invalid_result)
    assert response.status_code == 403
    assert "他のユーザーの解析結果は保存できません" in response.json()["detail"]

def test_save_analysis_result_invalid_risk_level(mock_firebase_service, mock_auth):
    """解析結果の保存（異常系：不正なリスクレベル）"""
    invalid_result = VALID_ANALYSIS_RESULT.copy()
    invalid_result["risk_level"] = "INVALID"
    
    response = client.post("/analysis/save", json=invalid_result)
    assert response.status_code == 400
    assert "無効なリスクレベルです" in response.json()["detail"]

def test_save_analysis_result_invalid_score(mock_firebase_service, mock_auth):
    """解析結果の保存（異常系：不正なスコア値）"""
    invalid_result = VALID_ANALYSIS_RESULT.copy()
    invalid_result["confidence_score"] = 1.5
    
    response = client.post("/analysis/save", json=invalid_result)
    assert response.status_code == 400
    assert "信頼度スコアは0から1の間である必要があります" in response.json()["detail"]

def test_get_analysis_history_success(mock_firebase_service, mock_auth):
    """解析履歴の取得（正常系）"""
    response = client.get("/analysis/history")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == MOCK_USER.user_id
    assert len(data["results"]) == 1

def test_get_analysis_history_with_limit(mock_firebase_service, mock_auth):
    """解析履歴の取得（正常系：件数制限あり）"""
    response = client.get("/analysis/history?limit=5")
    assert response.status_code == 200
    
    # FirebaseServiceのget_analysis_historyが正しいlimitで呼ばれたことを確認
    mock_firebase_service.return_value.get_analysis_history.assert_called_with(
        user_id=MOCK_USER.user_id,
        limit=5
    )

def test_get_analysis_history_unauthorized():
    """解析履歴の取得（異常系：未認証）"""
    # mock_authを使用しない
    response = client.get("/analysis/history")
    assert response.status_code == 401 