from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, initialize_app
from typing import Optional
import os
from dotenv import load_dotenv

from src.services.vision_service import VisionService
from src.services.gemini_service import GeminiService
from src.services.firestore_service import FirestoreService

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
    allow_origins=["*"],  # 本番環境では適切なオリジンに制限する
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
@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    user_id: str = None
):
    try:
        # 画像をバイト形式で読み込み
        contents = await file.read()
        
        # Vision AIで画像解析
        risk_score = vision_service.analyze_image(contents)
        
        # リスクレベルの判定
        risk_level = _calculate_risk_level(risk_score)
        
        # Gemini APIでアドバイス生成
        advice = gemini_service.generate_advice(risk_level)
        
        # Firestoreに結果を保存（ユーザーIDがある場合のみ）
        if user_id:
            doc_id = firestore_service.save_analysis_result(
                user_id=user_id,
                risk_score=risk_score,
                risk_level=risk_level,
                advice=advice
            )
        
        # 結果を返却
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "advice": advice
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"画像解析中にエラーが発生しました: {str(e)}"
        )

# 解析履歴取得エンドポイント
@app.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 10):
    try:
        history = firestore_service.get_user_history(user_id, limit)
        return {"history": history}
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
    uvicorn.run(app, host="0.0.0.0", port=8080)
