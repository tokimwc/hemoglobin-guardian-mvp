from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..services.firebase_service import FirebaseService
from ..models.analysis import AnalysisResult, AnalysisHistory
from ..models.auth import UserData
from .auth import get_current_user
from datetime import datetime
import json

router = APIRouter(prefix="/analysis", tags=["解析"])
firebase_service = FirebaseService()

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_analysis_result(
    result: AnalysisResult,
    current_user: UserData = Depends(get_current_user)
) -> dict:
    """解析結果を保存"""
    try:
        # ユーザーIDの検証
        if result.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="他のユーザーの解析結果は保存できません"
            )
        
        # リスクレベルの検証
        if result.risk_level not in ["LOW", "MEDIUM", "HIGH"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なリスクレベルです"
            )
        
        # 信頼度スコアの検証
        if not 0 <= result.confidence_score <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="信頼度スコアは0から1の間である必要があります"
            )
        
        # 画像品質スコアの検証
        if not 0 <= result.image_quality_score <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="画像品質スコアは0から1の間である必要があります"
            )
        
        # 栄養アドバイスの検証
        required_keys = ["summary", "iron_rich_foods", "meal_suggestions", "lifestyle_tips"]
        if not all(key in result.nutrition_advice for key in required_keys):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="栄養アドバイスに必要な情報が不足しています"
            )
        
        # 解析結果を保存
        doc_id = await firebase_service.save_analysis_result(result)
        
        return {
            "message": "解析結果を保存しました",
            "result_id": doc_id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析結果の保存に失敗しました: {str(e)}"
        )

@router.get("/history", response_model=AnalysisHistory)
async def get_analysis_history(
    limit: Optional[int] = 10,
    current_user: UserData = Depends(get_current_user)
) -> AnalysisHistory:
    """ユーザーの解析履歴を取得"""
    try:
        # 履歴の取得（デフォルトで最新10件）
        history = await firebase_service.get_analysis_history(
            user_id=current_user.user_id,
            limit=min(limit, 50)  # 最大50件まで
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析履歴の取得に失敗しました: {str(e)}"
        ) 