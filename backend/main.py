from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from src.middleware.rate_limiter import RateLimiter
from src.models.analysis import (
    NailAnalysisResult,
    ImageQualityMetrics,
    NutritionAdvice,
    AnalysisHistory,
    ErrorResponse
)
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import time
from src.utils.env_validator import EnvironmentValidator
import logging
import sys
import firebase_admin
from firebase_admin import credentials
from typing import Optional, Dict, Any, List
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from contextlib import asynccontextmanager
import redis.asyncio as redis
import imghdr  # 画像ファイル形式を検証するために追加

from src.services.vision_service import VisionService
from src.services.gemini_service import GeminiService
from src.services.firestore_service import FirestoreService

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

# 環境変数の読み込み（1回だけ）
load_dotenv(encoding='utf-8')  # UTF-8エンコーディングを明示的に指定

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
    openapi_prefix="" if os.getenv("TEST_MODE") == "True" else None,
    lifespan=lifespan
)

# レート制限の設定
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=True
)

app.state.limiter = limiter

# レート制限の有効/無効を環境変数で制御
DISABLE_RATE_LIMIT = os.getenv("DISABLE_RATE_LIMIT", "true").lower() == "true"

@app.on_event("startup")
async def startup():
    if DISABLE_RATE_LIMIT:
        logger.info("レート制限が無効化されています (テスト環境)")
    else:
        logger.info("レート制限が有効化されています")
    logger.info("レート制限を初期化しました")

# レート制限を環境変数で制御
is_rate_limit_enabled = os.environ.get("DISABLE_RATE_LIMIT") != "true"

if is_rate_limit_enabled:
    app.add_middleware(SlowAPIMiddleware)
else:
    print("レート制限が無効化されています (テスト環境)")

# CORS設定の取得
def get_cors_origins():
    origins = os.getenv("CORS_ORIGINS")
    if origins:
        return eval(origins)
    return ["http://localhost:3000"]  # デフォルト値

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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

# 許可するホストの設定を環境変数から読み込み
allowed_hosts = json.loads(os.getenv("ALLOWED_HOSTS", '["localhost", "127.0.0.1", "*"]'))
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
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

# カスタムミドルウェアでレート制限を実装
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """レート制限ミドルウェア"""
    if os.getenv("TEST_MODE") == "True":
        return await call_next(request)
        
    rate_limiter = get_rate_limiter(request)
    client_ip = request.client.host
    
    if rate_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail="リクエスト制限を超過しました。しばらく待ってから再試行してください。"
        )
    
    response = await call_next(request)
    remaining = rate_limiter.get_remaining(client_ip)
    
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    
    return response

# 画像解析エンドポイント
@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    user_id: str = None,
    request: Request = None
):
    try:
        logger.info(f"画像解析リクエストを受信: filename={file.filename}, content_type={file.content_type}")
        
        # ファイルの検証
        contents = await file.read()
        image_format = imghdr.what(None, contents)
        logger.info(f"検出された画像フォーマット: {image_format}")
        
        if not image_format:
            logger.error("無効なファイル形式")
            raise HTTPException(
                status_code=400,
                detail="無効なファイル形式です。JPEG、PNG、GIF形式の画像ファイルを使用してください。"
            )
        
        # ファイルポインタを先頭に戻す
        await file.seek(0)
        
        try:
            # Vision AIによる画像解析
            logger.info("Vision AI解析を開始")
            vision_result = await vision_service.analyze_image(contents)
            logger.info(f"Vision AI解析結果: {vision_result}")
            
            # Gemini APIによる栄養アドバイス生成
            logger.info("Gemini API解析を開始")
            nutrition_advice = await gemini_service.generate_advice(vision_result)
            logger.info(f"Gemini API解析結果: {nutrition_advice}")
            
            # 解析結果オブジェクトの作成
            result = NailAnalysisResult(
                risk_score=vision_result.get("risk_score", 0.5),
                confidence_score=vision_result.get("confidence_score", 0.8),
                risk_level=_calculate_risk_level(vision_result.get("risk_score", 0.5)),
                detected_colors=vision_result.get("detected_colors", []),
                quality_metrics=ImageQualityMetrics(
                    is_blurry=vision_result.get("is_blurry", False),
                    brightness_score=vision_result.get("brightness_score", 0.8),
                    has_proper_lighting=vision_result.get("has_proper_lighting", True),
                    has_detected_nail=vision_result.get("has_detected_nail", True)
                ),
                created_at=datetime.utcnow().isoformat(),
                user_id=user_id
            )
            
            # 認証されたユーザーの場合、結果を保存
            if user_id:
                logger.info(f"解析結果を保存: user_id={user_id}")
                analysis_history = AnalysisHistory(
                    history_id=str(int(time.time())),
                    user_id=user_id,
                    analysis_result=result,
                    nutrition_advice=nutrition_advice,
                    created_at=datetime.utcnow()
                )
                await firestore_service.save_analysis_result(
                    user_id=user_id,
                    analysis_result=analysis_history.dict()
                )
            
            return JSONResponse(
                content={
                    "analysis": result.dict(),
                    "nutrition_advice": nutrition_advice.dict() if nutrition_advice else None
                },
                status_code=200
            )
            
        except Exception as service_error:
            logger.error(f"サービス処理中にエラーが発生: {str(service_error)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"画像解析中にエラーが発生しました: {str(service_error)}"
            )

    except HTTPException as he:
        logger.error(f"HTTPエラーが発生: {he.detail}", exc_info=True)
        return JSONResponse(
            content=ErrorResponse(
                summary=he.detail,
                error_type="VALIDATION_ERROR" if he.status_code < 500 else "SYSTEM_ERROR"
            ).dict(),
            status_code=he.status_code
        )
    except Exception as e:
        logger.error(f"予期せぬエラーが発生: {str(e)}", exc_info=True)
        return JSONResponse(
            content=ErrorResponse(
                summary="画像の解析中に問題が発生しました。後ほど再度お試しください。",
                error_type="SYSTEM_ERROR",
                warnings=[f"エラーの詳細: {str(e)}"]
            ).dict(),
            status_code=500
        )

def _calculate_risk_level(risk_score: float) -> str:
    if risk_score < 0.3:
        return "low"
    elif risk_score > 0.7:
        return "high"
    return "medium"

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
