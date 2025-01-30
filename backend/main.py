from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, initialize_app
from typing import Optional, List
import os
from dotenv import load_dotenv
from datetime import datetime

from src.services.vision_service import VisionService
from src.services.gemini_service import GeminiService
from src.services.firestore_service import FirestoreService
from src.models.analysis import AnalysisResult, AnalysisHistory

# 環境変数の読み込み
load_dotenv()

app = FastAPI(
    title="ヘモグロビンガーディアン API",
    description="貧血リスク推定＆AIアドバイスを提供するバックエンドAPI",
    version="1.0.0"
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 開発環境
        "http://localhost:8080",  # 開発環境
        "https://hemoglobin-guardian-mvp-app.web.app",  # 本番環境（Firebase Hosting）
        os.getenv("FRONTEND_URL", ""),  # 環境変数から取得
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebaseの初期化
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
firebase_app = initialize_app(cred)

# サービスのインスタンス化
vision_service = VisionService()
gemini_service = GeminiService()
firestore_service = FirestoreService()

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# 画像解析エンドポイント
@app.post("/analyze", response_model=AnalysisResult)
async def analyze_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = None
):
    try:
        # 画像をバイト形式で読み込み
        contents = await file.read()
        
        # Vision AIで画像解析
        analysis = await vision_service.analyze_image(contents)
        
        # 信頼度が低い場合は警告を追加
        warnings = []
        if analysis.confidence_score < 0.5:
            if analysis.quality_metrics.is_blurry:
                warnings.append("画像がブレています")
            if not analysis.quality_metrics.has_proper_lighting:
                warnings.append("照明条件が適切ではありません")
            if not analysis.quality_metrics.has_detected_nail:
                warnings.append("爪が正しく検出できませんでした")
        
        # Gemini APIでアドバイス生成
        advice = await gemini_service.generate_advice(
            risk_level=_calculate_risk_level(analysis.risk_score),
            confidence_score=analysis.confidence_score,
            warnings=warnings
        )
        
        # 解析結果の作成
        result = AnalysisResult(
            risk_score=analysis.risk_score,
            risk_level=_calculate_risk_level(analysis.risk_score),
            advice=advice,
            confidence_score=analysis.confidence_score,
            warnings=warnings,
            quality_metrics={
                "is_blurry": analysis.quality_metrics.is_blurry,
                "brightness_score": analysis.quality_metrics.brightness_score,
                "has_proper_lighting": analysis.quality_metrics.has_proper_lighting,
                "has_detected_nail": analysis.quality_metrics.has_detected_nail
            },
            created_at=datetime.now()
        )
        
        # Firestoreに結果を保存（ユーザーIDがある場合のみ）
        if user_id:
            await firestore_service.save_analysis_result(
                user_id=user_id,
                analysis_result=result
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"画像解析中にエラーが発生しました: {str(e)}"
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

if __name__ == "__main__":
    import uvicorn
    import logging

    # ロギングの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

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
        timeout=timeout,
        proxy_headers=True,
        forwarded_allow_ips="*",
        access_log=True,
        log_level="info"
    )
