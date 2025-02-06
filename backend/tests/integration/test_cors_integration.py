import pytest
from fastapi.testclient import TestClient
from main import app
import json
import os
from pathlib import Path
import httpx
import base64
import io
from PIL import Image
import numpy as np

client = TestClient(app)

def test_cors_preflight(test_client: TestClient):
    """CORSプリフライトリクエストのテスト"""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type, authorization",
        "Host": "testserver"
    }
    response = test_client.options("/analyze", headers=headers)
    
    assert response.status_code == 200, f"Response: {response.text}"
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "authorization" in response.headers["access-control-allow-headers"].lower()

def test_security_headers(test_client: TestClient):
    """セキュリティヘッダーのテスト"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-xss-protection"] == "1; mode=block"
    assert "max-age=31536000" in response.headers["strict-transport-security"]
    assert "default-src 'self'" in response.headers["content-security-policy"]

def test_rate_limit_headers(test_client: TestClient):
    """レート制限ヘッダーのテスト"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    assert "x-ratelimit-reset" in response.headers

def test_rate_limit_exceeded(test_client: TestClient):
    """レート制限超過のテスト"""
    # レート制限を超えるまでリクエストを送信
    for _ in range(int(test_client.app.state.rate_limiter.requests_per_minute) + 1):
        test_client.get("/health")
    
    # 次のリクエストはレート制限エラーになるはず
    response = test_client.get("/health")
    assert response.status_code == 429
    # Headersオブジェクトを小文字のキーの辞書に変換
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    # "retry-after" ヘッダーの存在を確認
    assert "retry-after" in headers_lower, "Retry-After header is missing"

def create_test_image():
    """テスト用の画像データを生成"""
    # 100x100の白い画像を作成
    img = Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_analyze_endpoint_cors():
    """画像解析エンドポイントのCORS設定をテスト"""
    client = TestClient(app)
    
    # テスト用の画像を作成
    test_image = create_test_image()
    
    # CORSヘッダーを設定
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    
    # 画像ファイルとしてPOSTリクエストを送信
    files = {
        "file": ("test_image.jpg", test_image, "image/jpeg")
    }
    
    response = client.post(
        "/analyze",
        headers=headers,
        files=files,
        params={"user_id": "test-user"}
    )
    
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    
    # レスポンスの内容を確認
    response_data = response.json()
    assert "analysis_data" in response_data
    assert "risk_score" in response_data
    assert "advice" in response_data

def test_invalid_origin(test_client: TestClient):
    """無効なオリジンからのリクエストのテスト"""
    response = test_client.get(
        "/health",
        headers={"Origin": "http://malicious-site.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

@pytest.mark.asyncio
async def test_analyze_with_auth():
    """認証付きの画像解析リクエストのテスト"""
    test_image_path = Path("tests/test_data/test_nail2.jpg")
    assert test_image_path.exists(), "テスト用画像ファイルが見つかりません"

    headers = {
        "Origin": "http://localhost:3000",
        "Authorization": "Bearer test-token"
    }
    
    with open(test_image_path, "rb") as f:
        files = {"file": ("test_nail2.jpg", f, "image/jpeg")}
        response = client.post(
            "/analyze",
            files=files,
            headers=headers,
            params={"user_id": "test-user"}
        )
    
    assert response.status_code == 200
    result = response.json()
    assert "risk_score" in result
    assert "advice" in result
    assert "warnings" in result 