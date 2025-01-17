from typing import List, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import os
from ..models.analysis import AnalysisResult, UserProfile, AnalysisHistory

class FirebaseService:
    """Firestore操作を担当するサービスクラス"""
    
    def __init__(self):
        # Firebase初期化（未初期化の場合のみ）
        if not firebase_admin._apps:
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            if not cred_path:
                raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable is not set")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        
    async def save_analysis_result(self, result: AnalysisResult) -> str:
        """解析結果を保存"""
        try:
            # 解析結果をFirestoreに保存
            doc_ref = self.db.collection('analysis_results').document()
            doc_ref.set(result.to_dict())
            
            # ユーザーの解析カウントを更新
            user_ref = self.db.collection('users').document(result.user_id)
            user_ref.update({
                'analysis_count': firestore.Increment(1)
            })
            
            # 解析履歴を更新
            await self._update_analysis_history(result)
            
            return doc_ref.id
        except Exception as e:
            raise Exception(f"Failed to save analysis result: {str(e)}")
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """ユーザープロファイルを取得"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return UserProfile.from_dict(doc.to_dict())
            return None
        except Exception as e:
            raise Exception(f"Failed to get user profile: {str(e)}")
    
    async def create_user_profile(self, email: str, user_id: str) -> UserProfile:
        """新規ユーザープロファイルを作成"""
        try:
            now = datetime.utcnow().isoformat()
            profile = UserProfile(
                user_id=user_id,
                email=email,
                created_at=now,
                last_login=now
            )
            
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.set(profile.to_dict())
            
            return profile
        except Exception as e:
            raise Exception(f"Failed to create user profile: {str(e)}")
    
    async def update_last_login(self, user_id: str):
        """最終ログイン日時を更新"""
        try:
            doc_ref = self.db.collection('users').document(user_id)
            doc_ref.update({
                'last_login': datetime.utcnow().isoformat()
            })
        except Exception as e:
            raise Exception(f"Failed to update last login: {str(e)}")
    
    async def get_analysis_history(self, user_id: str, limit: int = 10) -> AnalysisHistory:
        """ユーザーの解析履歴を取得"""
        try:
            # 最新のN件の解析結果を取得
            results_ref = self.db.collection('analysis_results')\
                .where('user_id', '==', user_id)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            results = []
            for doc in results_ref.stream():
                result_data = doc.to_dict()
                results.append(AnalysisResult.from_dict(result_data))
            
            return AnalysisHistory(
                user_id=user_id,
                results=results,
                last_updated=datetime.utcnow().isoformat()
            )
        except Exception as e:
            raise Exception(f"Failed to get analysis history: {str(e)}")
    
    async def _update_analysis_history(self, result: AnalysisResult):
        """解析履歴を更新（内部メソッド）"""
        try:
            history_ref = self.db.collection('analysis_histories').document(result.user_id)
            history_doc = history_ref.get()
            
            if history_doc.exists:
                # 既存の履歴を更新
                history_data = history_doc.to_dict()
                history = AnalysisHistory.from_dict(history_data)
                history.results.insert(0, result)  # 新しい結果を先頭に追加
                history.last_updated = datetime.utcnow().isoformat()
                
                # 最新の10件のみ保持
                if len(history.results) > 10:
                    history.results = history.results[:10]
                
                history_ref.set(history.to_dict())
            else:
                # 新規履歴を作成
                history = AnalysisHistory(
                    user_id=result.user_id,
                    results=[result],
                    last_updated=datetime.utcnow().isoformat()
                )
                history_ref.set(history.to_dict())
        except Exception as e:
            raise Exception(f"Failed to update analysis history: {str(e)}") 