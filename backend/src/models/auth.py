from pydantic import BaseModel
from typing import Optional

class UserData(BaseModel):
    """ユーザー情報を表すモデル"""
    user_id: str
    email: str
    analysis_count: int = 0

class AuthResponse(BaseModel):
    """認証レスポンスを表すモデル"""
    message: str
    user: UserData 