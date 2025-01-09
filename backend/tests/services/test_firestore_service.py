import pytest
from unittest.mock import Mock, patch
import firebase_admin
from firebase_admin import credentials
from datetime import datetime
from src.services.firestore_service import FirestoreService

@pytest.fixture(scope="session", autouse=True)
def setup_firebase():
    """テスト用のFirebase初期化"""
    try:
        firebase_admin.get_app()
    except ValueError:
        # テスト用のモック認証情報
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': 'mock-project-id',
        })

@pytest.fixture
def firestore_service():
    """Firestoreサービスのモック"""
    with patch('firebase_admin.firestore.client') as mock_client:
        service = FirestoreService()
        service.db = mock_client.return_value
        return service

def test_save_analysis_result(firestore_service):
    """解析結果保存のテスト"""
    # テストデータ
    user_id = "test_user"
    risk_score = 0.7
    risk_level = "HIGH"
    advice = "テストアドバイス"
    
    # モックの設定
    mock_doc_ref = Mock()
    firestore_service.db.collection().document().collection().document.return_value = mock_doc_ref
    
    # 関数実行
    doc_id = firestore_service.save_analysis_result(
        user_id=user_id,
        risk_score=risk_score,
        risk_level=risk_level,
        advice=advice
    )
    
    # 検証
    firestore_service.db.collection.assert_called_with('users')
    mock_doc_ref.set.assert_called_once()

def test_get_user_history(firestore_service):
    """履歴取得のテスト"""
    # テストデータ
    user_id = "test_user"
    test_datetime = datetime.now()
    mock_docs = [
        Mock(to_dict=lambda: {
            "risk_score": 0.7,
            "risk_level": "HIGH",
            "advice": "テストアドバイス",
            "created_at": test_datetime
        }, id="test_doc_id")
    ]
    
    # モックの設定
    mock_collection_ref = Mock()
    mock_collection_ref.order_by().limit().stream.return_value = mock_docs
    firestore_service.db.collection().document().collection.return_value = mock_collection_ref
    
    # 関数実行
    history = firestore_service.get_user_history(user_id, limit=5)
    
    # 検証
    assert len(history) == 1
    assert history[0]["risk_level"] == "HIGH"
    assert "created_at" in history[0]
    assert history[0]["id"] == "test_doc_id" 