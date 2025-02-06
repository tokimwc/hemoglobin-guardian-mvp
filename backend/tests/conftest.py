import pytest
from datetime import datetime, timezone
import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# テスト環境変数の設定
os.environ["TEST_MODE"] = "True"

# .env.testファイルの読み込み
env_file = Path(__file__).parent.parent / ".env.test"
load_dotenv(env_file)

# アプリケーションのインポート（環境変数設定後）
from main import app
from tests.mocks.mock_services import (
    MockVisionService,
    MockGeminiService,
    MockFirestoreService
)

@pytest.fixture(autouse=True)
def setup_test_env():
    """テスト環境のセットアップ"""
    # 環境変数の設定
    os.environ["FIREBASE_CREDENTIALS_PATH"] = "tests/mock_credentials.json"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
    os.environ["VERTEX_AI_LOCATION"] = "us-central1"
    os.environ["GEMINI_MODEL_ID"] = "gemini-1.5-pro"
    
    # モックの認証情報ファイルを作成
    if not os.path.exists("tests/mock_credentials.json"):
        mock_creds = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "mock_key_id",
            "private_key": "mock_private_key",
            "client_email": "mock@test-project.iam.gserviceaccount.com",
            "client_id": "mock_client_id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock"
        }
        os.makedirs("tests", exist_ok=True)
        with open("tests/mock_credentials.json", "w") as f:
            json.dump(mock_creds, f)
    
    yield
    
    # テスト後のクリーンアップ
    if os.path.exists("tests/mock_credentials.json"):
        os.remove("tests/mock_credentials.json")

@pytest.fixture
def utc_now():
    """現在のUTC時刻を返す"""
    return datetime.now(timezone.utc)

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """テスト環境変数の読み込み"""
    env_file = Path(__file__).parent.parent / ".env.test"
    load_dotenv(env_file)

@pytest.fixture
def test_client():
    """テストクライアントの作成（ミドルウェアは main.py ですでに追加済み）"""
    return TestClient(app, base_url="http://testserver")

@pytest.fixture
def mock_vision_service():
    """Vision AIサービスのモック"""
    return MockVisionService()

@pytest.fixture
def mock_gemini_service():
    """Gemini APIサービスのモック"""
    return MockGeminiService()

@pytest.fixture
def mock_firestore_service():
    """Firestoreサービスのモック"""
    return MockFirestoreService()

@pytest.fixture
def test_image_path():
    """テスト用画像のパス"""
    return Path(__file__).parent / "test_data" / "test_nail2.jpg"

@pytest.fixture
def mock_user_id():
    """モックユーザーID"""
    return "test_user_123"

class MockGeminiService:
    def __init__(self, *args, **kwargs):
        pass

    async def generate_advice(self, image_content):
        return {
            "predictions": [
                {"risk_level": "low", "advice": "Mock advice for low risk"}
            ]
        } 