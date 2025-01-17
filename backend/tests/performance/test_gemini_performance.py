import pytest
import asyncio
import time
import psutil
import os
from src.services.gemini_service import GeminiService
from typing import List

@pytest.fixture
def gemini_service():
    """Gemini APIサービスのインスタンス"""
    return GeminiService()

async def wait_for_quota_reset():
    """APIクォータのリセットを待つ"""
    await asyncio.sleep(10)  # 10秒待機に変更

@pytest.mark.performance
@pytest.mark.asyncio
async def test_response_time(gemini_service):
    """応答時間のテスト"""
    await wait_for_quota_reset()
    start_time = time.time()
    
    result = await gemini_service.generate_advice(
        risk_level="MEDIUM",
        confidence_score=0.8,
        warnings=[]
    )
    
    end_time = time.time()
    response_time = end_time - start_time
    
    # 応答時間は10秒以内であることを確認（Gemini APIの実際の応答時間を考慮）
    assert response_time < 10.0, f"応答時間が遅すぎます: {response_time:.2f}秒"
    assert result is not None

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_requests(gemini_service):
    """同時リクエスト処理のテスト"""
    await wait_for_quota_reset()
    num_requests = 2
    start_time = time.time()
    
    # 複数のリクエストを同時に実行
    tasks = [
        gemini_service.generate_advice(
            risk_level="MEDIUM",
            confidence_score=0.8,
            warnings=[]
        )
        for _ in range(num_requests)
    ]
    
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / num_requests
    
    # 全てのリクエストが成功していることを確認
    assert len(results) == num_requests
    assert all(result is not None for result in results)
    
    # 平均応答時間は8秒以内であることを確認
    assert avg_time < 8.0, f"平均応答時間が遅すぎます: {avg_time:.2f}秒"

@pytest.mark.performance
def test_memory_usage(gemini_service):
    """メモリ使用量のテスト"""
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024  # MB単位
    
    # 同期的にアドバイスを生成
    asyncio.run(gemini_service.generate_advice(
        risk_level="MEDIUM",
        confidence_score=0.8,
        warnings=[]
    ))
    
    end_memory = process.memory_info().rss / 1024 / 1024  # MB単位
    memory_increase = end_memory - start_memory
    
    # メモリ増加量は50MB以内であることを確認
    assert memory_increase < 50, f"メモリ使用量が多すぎます: {memory_increase:.2f}MB増加"

@pytest.mark.performance
@pytest.mark.asyncio
async def test_error_handling_performance(gemini_service):
    """エラー時の応答時間とメモリ使用量のテスト"""
    await wait_for_quota_reset()
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024
    start_time = time.time()
    
    # 無効なパラメータでエラーを発生させる
    result = await gemini_service.generate_advice(
        risk_level="INVALID",  # 無効なリスクレベル
        confidence_score=-1.0,  # 無効な信頼度スコア
        warnings=["エラーテスト"]
    )
    
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024
    
    response_time = end_time - start_time
    memory_increase = end_memory - start_memory
    
    # エラー時でも応答は5秒以内であることを確認（最適化後）
    assert response_time < 5.0, f"エラー時の応答が遅すぎます: {response_time:.2f}秒"
    # エラー時のメモリ増加は10MB以内であることを確認
    assert memory_increase < 10, f"エラー時のメモリ使用量が多すぎます: {memory_increase:.2f}MB増加"
    # エラーレスポンスが正しく返されることを確認
    assert result is not None
    assert "申し訳ありません" in result.summary
    assert len(result.warnings) > 0
    assert "エラー" in result.warnings[0]
    assert len(result.iron_rich_foods) > 0
    assert len(result.meal_suggestions) > 0
    assert len(result.lifestyle_tips) > 0

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_error_handling(gemini_service):
    """エラー時の同時リクエスト処理のテスト"""
    await wait_for_quota_reset()
    num_requests = 2
    start_time = time.time()
    
    # 複数の無効なリクエストを同時に実行
    tasks = [
        gemini_service.generate_advice(
            risk_level="INVALID",
            confidence_score=-1.0,
            warnings=["エラーテスト"]
        )
        for _ in range(num_requests)
    ]
    
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / num_requests
    
    # エラー時の平均応答時間は5秒以内であることを確認
    assert avg_time < 5.0, f"エラー時の平均応答時間が遅すぎます: {avg_time:.2f}秒"
    # 全てのリクエストが正しく処理されていることを確認
    assert len(results) == num_requests
    assert all(result is not None for result in results)
    assert all("申し訳ありません" in result.summary for result in results)
    assert all(len(result.warnings) > 0 for result in results)
    assert all("エラー" in result.warnings[0] for result in results) 