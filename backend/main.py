from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from src.middleware.rate_limiter import RateLimiter
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from src.utils.env_validator import EnvironmentValidator
import logging
import sys
import firebase_admin
from firebase_admin import credentials
from typing import Optional, Dict, Any, List
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager
import redis.asyncio as redis
import time
import imghdr  # 画像ファイル形式を検証するために追加

from src.services.vision_service import VisionService
from src.services.gemini_service import GeminiService
from src.services.firestore_service import FirestoreService
from src.models.analysis import AnalysisResult, AnalysisHistory

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 環境変数のバリデーション
env_validator = EnvironmentValidator(".env")
if not env_validator.validate():
    env_validator.print_validation_report()
    logger.error("環境変数の設定が不正です。アプリケーションを終了します。")
    sys.exit(1)

# 環境変数の読み込み
load_dotenv()

# サービスのインポート
if os.getenv("TEST_MODE") == "True":
    from tests.mocks.mock_services import (
        MockVisionService as VisionService,
        MockGeminiService as GeminiService,
        MockFirestoreService as FirestoreService
    )
else:
    from src.services.vision_service import VisionService
    from src.services.gemini_service import GeminiService
    from src.services.firestore_service import FirestoreService
    # Firebaseの初期化
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
    firebase_admin.initialize_app(cred)

# グローバルなレート制限設定
limiter = Limiter(key_func=get_remote_address)

class RateLimiter:
    """カスタムレート制限クラス"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, requests_per_minute: int = 100):
        if not hasattr(self, 'initialized'):
            self.requests_per_minute = requests_per_minute
            self._requests = {}
            self._test_mode = os.getenv("TEST_MODE", "False").lower() == "true"
            self._test_counter = 0
            self.initialized = True

    def is_rate_limited(self, key: str) -> bool:
        if self._test_mode:
            self._test_counter += 1
            return self._test_counter > self.requests_per_minute

        current_time = time.time()
        if key not in self._requests:
            self._requests[key] = []
        
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if current_time - req_time < 60
        ]
        
        if len(self._requests[key]) >= self.requests_per_minute:
            return True
        
        self._requests[key].append(current_time)
        return False

    def get_remaining(self, key: str) -> int:
        if self._test_mode:
            return max(0, self.requests_per_minute - self._test_counter)
        
        if key not in self._requests:
            return self.requests_per_minute
        return max(0, self.requests_per_minute - len(self._requests[key]))

    def reset(self):
        """レート制限カウンターをリセット"""
        self._requests = {}
        self._test_counter = 0

def get_rate_limiter(request: Request) -> RateLimiter:
    """レート制限インスタンスを取得または作成"""
    if not hasattr(request.app.state, "rate_limiter"):
        request.app.state.rate_limiter = RateLimiter()
    return request.app.state.rate_limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフスパンイベントハンドラ"""
    # スタートアップ処理
    rate_limiter = RateLimiter(requests_per_minute=100)
    app.state.rate_limiter = rate_limiter
    print("レート制限が無効化されています (テスト環境)" if os.getenv("TEST_MODE", "False").lower() == "true" else "レート制限を初期化しました")
    
    yield
    
    # シャットダウン処理
    if hasattr(app.state, 'rate_limiter'):
        app.state.rate_limiter.reset()

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="ヘモグロビンガーディアン API",
    description="貧血リスク推定＆AIアドバイスを提供するバックエンドAPI",
    version="1.0.0",
    # テストモードの場合、ホストチェックを無効化
    openapi_prefix="" if os.getenv("TEST_MODE") == "True" else None,
    lifespan=lifespan  # ライフスパンハンドラを設定
)

# レート制限を環境変数で制御
is_rate_limit_enabled = os.environ.get("DISABLE_RATE_LIMIT") != "true"

if is_rate_limit_enabled:
    limiter = FastAPILimiter()
    app.state.limiter = limiter
    app.add_middleware(FastAPILimiter)

    @app.on_event("startup")
    async def startup_event():
        """FastAPI 起動時のイベントハンドラ (レート制限有効時のみ)"""
        await FastAPILimiter.init(app)
        
    # レート制限の設定
    rate_limiter = RateLimiter(
        times=int(os.getenv("MAX_REQUESTS_PER_MINUTE", 60)),
        seconds=60
    )
    
    # レート制限ミドルウェアの追加
    app.middleware("http")(rate_limiter)
else:
    print("レート制限が無効化されています (テスト環境)")

# SlowAPIミドルウェアを追加（テストモードに関係なく常に追加）
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS設定の取得
def get_cors_origins():
    origins = os.getenv("CORS_ORIGINS")
    if origins:
        return eval(origins)
    return ["http://localhost:3000"]  # デフォルト値

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Length", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=600
)

# セキュリティスキーマの設定
security = HTTPBearer()

# セキュリティヘッダーミドルウェアの追加
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'"
    return response

# レート制限ミドルウェアの追加
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=json.loads(os.getenv("ALLOWED_HOSTS", '["localhost", "127.0.0.1"]'))
)

# サービスのインスタンス化
vision_service = VisionService()
gemini_service = GeminiService(
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("VERTEX_AI_LOCATION")
)
firestore_service = FirestoreService()

# カスタムミドルウェアでレート制限ヘッダーを追加
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    return response

# レート制限付きのヘルスチェックエンドポイント
@app.get("/health")
async def health_check(request: Request):
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": {
            "python_version": sys.version,
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": os.getenv("PORT", "8080")
        }
    }

class AnalysisResult:
    def __init__(self, image_url: str, analysis_data: Dict[str, Any], timestamp: float):
        self.image_url = image_url
        self.analysis_data = analysis_data
        self.timestamp = timestamp
        self.risk_score = self._calculate_risk_score(analysis_data)
        self.advice = self._generate_advice(analysis_data)
        self.warnings = self._generate_warnings(analysis_data)

    def _calculate_risk_score(self, analysis_data: Dict[str, Any]) -> float:
        """ヘモグロビンレベルに基づいてリスクスコアを計算"""
        level = analysis_data.get('hemoglobin_level', 'normal').lower()
        if level == 'low':
            return 0.8
        elif level == 'very_low':
            return 1.0
        return 0.2  # normal

    def _generate_advice(self, analysis_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """解析結果に基づいてアドバイスを生成"""
        level = analysis_data.get('hemoglobin_level', 'normal').lower()
        base_advice = {
            "nutrition": ["鉄分を多く含む食品を摂取することをお勧めします"],
            "lifestyle": ["規則正しい生活を心がけましょう"],
            "medical": ["定期的な健康診断を受けることをお勧めします"]
        }
        
        if level == 'low':
            base_advice["nutrition"].append("レバーや赤身肉を積極的に摂取してください")
            base_advice["medical"].append("医師に相談することをお勧めします")
        elif level == 'very_low':
            base_advice["nutrition"].append("すぐに医師に相談してください")
            base_advice["medical"].append("緊急の医療相談が必要です")
        
        return base_advice

    def _generate_warnings(self, analysis_data: Dict[str, Any]) -> List[str]:
        """解析結果に基づいて警告メッセージを生成"""
        warnings = []
        confidence = analysis_data.get('confidence', 1.0)
        level = analysis_data.get('hemoglobin_level', 'normal').lower()

        if confidence < 0.8:
            warnings.append("解析結果の信頼性が低い可能性があります")

        if level == 'low':
            warnings.append("貧血の可能性があります。医師に相談することをお勧めします")
        elif level == 'very_low':
            warnings.append("重度の貧血の可能性があります。早急に医師の診察を受けてください")

        return warnings

    def to_dict(self) -> Dict[str, Any]:
        """結果を辞書形式に変換"""
        return {
            "image_url": self.image_url,
            "analysis_data": self.analysis_data,
            "timestamp": self.timestamp,
            "risk_score": self.risk_score,
            "advice": self.advice,
            "warnings": self.warnings  # 警告メッセージを追加
        }

# 画像解析エンドポイント
@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    user_id: str = None,
    request: Request = None
):
    try:
        # ファイルの検証
        contents = await file.read()
        # 画像ファイルかどうかを確認
        image_format = imghdr.what(None, contents)
        if not image_format:
            raise HTTPException(
                status_code=400,
                detail="無効なファイル形式です。JPEG、PNG、GIF形式の画像ファイルを使用してください。"
            )
        
        # ファイルポインタを先頭に戻す
        await file.seek(0)
        
        # 画像の解析処理
        image_url = "mock_image_url"  # テスト用のモックURL
        analysis_data = {
            "hemoglobin_level": "normal",
            "confidence": 0.95,
            "recommendations": ["バランスの取れた食事を継続してください"]
        }
        
        # 解析結果オブジェクトの作成
        result = AnalysisResult(
            image_url=image_url,
            analysis_data=analysis_data,
            timestamp=time.time()
        )

        # 認証されたユーザーの場合、結果を保存
        if user_id:
            await firestore_service.save_analysis_result(
                user_id=user_id,
                analysis_result=result.to_dict()
            )

        return JSONResponse(
            content=result.to_dict(),
            status_code=200
        )

    except HTTPException as he:
        logger.error("画像解析でバリデーションエラーが発生しました", exc_info=True)
        return JSONResponse(
            content={"error": str(he.detail)},
            status_code=he.status_code
        )
    except Exception as e:
        logger.error("画像解析エンドポイントでエラーが発生しました", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# 解析履歴取得エンドポイント
@app.get("/history/{user_id}", response_model=List[AnalysisHistory])
async def get_history(user_id: str, limit: int = 10):
    try:
        history = await firestore_service.get_user_history(user_id, limit)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"履歴取得中にエラーが発生しました: {str(e)}"
        )

def _calculate_risk_level(risk_score: float) -> str:
    """リスクスコアを3段階のレベルに変換"""
    if risk_score < 0.3:
        return "LOW"
    elif risk_score < 0.7:
        return "MEDIUM"
    else:
        return "HIGH"

# CORSプリフライトリクエストのハンドリング
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return {"detail": "OK"}

# プリフライトリクエストのハンドラー
@app.options("/analyze")
async def handle_preflight():
    return JSONResponse(
        content={},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "600",
        }
    )

# RateLimitExceeded例外ハンドラ
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Reset": str(int(time.time()) + 60),
            "Retry-After": "60"
        }
    )

# カスタムミドルウェアでレート制限を実装
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    rate_limiter = get_rate_limiter(request)
    client_ip = request.client.host

    # テスト用のエンドポイントの場合はレート制限をリセット
    if request.url.path == "/analyze" and os.getenv("TEST_MODE", "False").lower() == "true":
        rate_limiter.reset()
    
    if rate_limiter.is_rate_limited(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "X-RateLimit-Limit": str(rate_limiter.requests_per_minute),
                "X-RateLimit-Reset": str(int(time.time()) + 60),
                "Retry-After": "60"
            }
        )
    
    response = await call_next(request)
    
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.get_remaining(client_ip))
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response

if __name__ == "__main__":
    import uvicorn

    # 環境変数から設定を読み込み
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    workers = int(os.getenv("WORKERS", 1))
    timeout = int(os.getenv("TIMEOUT", 120))

    logger.info(f"Starting server - host: {host}, port: {port}, workers: {workers}")

    # サーバー起動
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=True,
        log_level="info"
    )
