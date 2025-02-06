import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from main import app
from pathlib import Path
import aiohttp
import statistics
from httpx import AsyncClient
import logging
from typing import List
import os
import psutil
from PIL import Image
import numpy as np
import io

logger = logging.getLogger(__name__)

async def measure_response_time(client: TestClient, test_id: int) -> float:
    """単一のリクエストの応答時間を測定"""
    start_time = time.time()
    try:
        response = client.get("/health")
        end_time = time.time()
        assert response.status_code == 200
        return end_time - start_time
    except Exception as e:
        logger.error(f"リクエスト {test_id} でエラーが発生: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_concurrent_requests():
    """同時リクエストのパフォーマンステスト"""
    num_requests = 10
    client = TestClient(app)
    
    # 非同期タスクのリストを作成
    tasks = [
        asyncio.create_task(measure_response_time(client, i))
        for i in range(num_requests)
    ]
    
    # すべてのタスクを実行して結果を待機
    results = await asyncio.gather(*tasks)
    
    # 応答時間の統計を計算
    avg_response_time = sum(results) / len(results)
    max_response_time = max(results)
    
    logger.info(f"平均応答時間: {avg_response_time:.3f}秒")
    logger.info(f"最大応答時間: {max_response_time:.3f}秒")
    
    # パフォーマンス基準を確認
    assert avg_response_time < 0.5, f"平均応答時間が遅すぎます: {avg_response_time:.3f}秒"
    assert max_response_time < 1.0, f"最大応答時間が遅すぎます: {max_response_time:.3f}秒"

def create_test_image():
    """テスト用の画像データを生成"""
    # 100x100の白い画像を作成
    array = np.full((100, 100, 3), 255, dtype=np.uint8)
    image = Image.fromarray(array)
    
    # BytesIOオブジェクトに画像を保存
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)
    
    return img_byte_arr

@pytest.mark.asyncio
async def test_image_analysis_performance():
    """画像解析のパフォーマンステスト"""
    client = TestClient(app)
    
    # テスト用の画像を生成
    test_image = create_test_image()
    
    start_time = time.time()
    
    # 画像ファイルとしてPOSTリクエストを送信
    files = {
        "file": ("test_image.jpg", test_image, "image/jpeg")
    }
    
    response = client.post(
        "/analyze",
        files=files,
        params={"user_id": "test-user"}
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # レスポンスの検証
    assert response.status_code == 200, f"予期しないステータスコード: {response.status_code}, レスポンス: {response.text}"
    
    # パフォーマンス基準の検証
    logger.info(f"画像解析処理時間: {processing_time:.3f}秒")
    assert processing_time < 5.0, f"画像解析が遅すぎます: {processing_time:.3f}秒"
    
    # レスポンスの内容を確認
    response_data = response.json()
    assert "analysis_data" in response_data
    assert "risk_score" in response_data
    assert "advice" in response_data

def test_memory_usage():
    """メモリ使用量のテスト"""
    client = TestClient(app)
    process = psutil.Process()
    
    # 初期メモリ使用量を記録
    initial_memory = process.memory_info().rss / 1024 / 1024  # MBに変換
    
    # 複数回リクエストを送信してメモリ使用量を測定
    headers = {"Origin": "http://localhost:3000"}
    for _ in range(50):
        response = client.get("/health", headers=headers)
        assert response.status_code == 200
    
    # 最終メモリ使用量を記録
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    logger.info(f"初期メモリ使用量: {initial_memory:.2f}MB")
    logger.info(f"最終メモリ使用量: {final_memory:.2f}MB")
    logger.info(f"メモリ増加量: {memory_increase:.2f}MB")
    
    # メモリ増加量が許容範囲内かチェック
    assert memory_increase < 50, f"メモリ使用量の増加が大きすぎます: {memory_increase:.2f}MB"

@pytest.mark.asyncio
async def test_error_handling_performance():
    """エラーハンドリングのパフォーマンステスト"""
    client = TestClient(app)
    
    # 無効なリクエストを送信して応答時間を測定
    start_time = time.time()
    
    response = client.post(
        "/analyze",
        files={"file": ("test.txt", b"invalid image data", "text/plain")},
        params={"user_id": "test-user"}
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # エラーレスポンスの検証
    assert response.status_code == 400
    assert "error" in response.json()
    
    # エラー処理の応答時間を検証
    logger.info(f"エラー処理時間: {processing_time:.3f}秒")
    assert processing_time < 1.0, f"エラー処理が遅すぎます: {processing_time:.3f}秒"
    
    # エラーメッセージの形式を検証
    error_response = response.json()
    assert isinstance(error_response["error"], str) 