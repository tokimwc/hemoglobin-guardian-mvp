from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from typing import Dict, Tuple, Optional
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_limit: int = 120,
        expire_time: int = 60
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.expire_time = expire_time
        self.requests: Dict[str, list] = {}
        self.cleanup_task = None

    async def init(self):
        """非同期クリーンアップタスクの初期化"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self):
        """期限切れのリクエスト記録をクリーンアップ"""
        while True:
            now = time.time()
            for ip in list(self.requests.keys()):
                self.requests[ip] = [
                    req_time for req_time in self.requests[ip]
                    if now - req_time < self.expire_time
                ]
                if not self.requests[ip]:
                    del self.requests[ip]
            await asyncio.sleep(10)  # 10秒ごとにクリーンアップ

    def _get_client_ip(self, request: Request) -> str:
        """クライアントIPアドレスの取得"""
        return request.client.host

    async def __call__(self, request: Request, call_next):
        """レート制限の実施"""
        # /analyze エンドポイントはレート制限対象外にする
        if request.url.path == "/analyze":
            return await call_next(request)
        
        await self.init()

        client_ip = self._get_client_ip(request)
        now = time.time()

        # リクエスト記録の初期化
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # 期限切れのリクエストを削除
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.expire_time
        ]

        # リクエスト数のチェック
        request_count = len(self.requests[client_ip])

        # バーストリミットのチェック
        if request_count >= self.burst_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "リクエスト制限を超過しました。しばらく待ってから再試行してください。",
                    "retry_after": self.expire_time
                },
                headers={"Retry-After": str(self.expire_time)}
            )

        # 通常のレート制限チェック
        if request_count >= self.requests_per_minute:
            window_start = now - 60  # 1分間のウィンドウ
            requests_in_window = len([
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ])
            
            if requests_in_window >= self.requests_per_minute:
                retry_after_seconds = int(window_start + 60 - now)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "リクエスト制限を超過しました。しばらく待ってから再試行してください。",
                        "retry_after": retry_after_seconds
                    },
                    headers={"Retry-After": str(retry_after_seconds)}
                )

        # リクエストを記録
        self.requests[client_ip].append(now)

        # レスポンスヘッダーの準備
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(now + self.expire_time))

        return response 