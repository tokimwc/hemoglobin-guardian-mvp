from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from typing import Optional
from datetime import datetime
from ..services.firebase_service import FirebaseService
from ..models.auth import AuthResponse, UserData
import json

router = APIRouter(prefix="/auth", tags=["認証"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
firebase_service = FirebaseService()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserData:
    """Firebase IDトークンを検証してユーザー情報を取得"""
    try:
        # トークンの検証
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        
        # ユーザープロファイルの取得
        profile = await firebase_service.get_user_profile(user_id)
        if not profile:
            # プロファイルが存在しない場合は作成
            firebase_user = auth.get_user(user_id)
            profile = await firebase_service.create_user_profile(
                email=firebase_user.email,
                user_id=user_id
            )
        
        # 最終ログイン時刻を更新
        await firebase_service.update_last_login(user_id)
        
        return UserData(
            user_id=profile.user_id,
            email=profile.email,
            analysis_count=profile.analysis_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/verify-token", response_model=AuthResponse)
async def verify_token(token: str = Depends(oauth2_scheme)) -> AuthResponse:
    """IDトークンを検証してユーザー情報を返却"""
    user = await get_current_user(token)
    return AuthResponse(
        message="認証成功",
        user=user
    )

@router.get("/user-profile", response_model=UserData)
async def get_user_profile(user: UserData = Depends(get_current_user)) -> UserData:
    """現在のユーザープロファイルを取得"""
    return user 