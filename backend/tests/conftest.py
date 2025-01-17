import pytest
from datetime import datetime, timezone
import os
import json

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