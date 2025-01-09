from firebase_admin import firestore
from datetime import datetime
from typing import List, Dict, Any

class FirestoreService:
    def __init__(self):
        self.db = firestore.client()
        
    def save_analysis_result(
        self,
        user_id: str,
        risk_score: float,
        risk_level: str,
        advice: str
    ) -> str:
        """
        解析結果をFirestoreに保存
        
        Args:
            user_id: ユーザーID
            risk_score: リスクスコア（0.0 ~ 1.0）
            risk_level: リスクレベル（"LOW", "MEDIUM", "HIGH"）
            advice: 生成されたアドバイス文
            
        Returns:
            str: 保存されたドキュメントのID
        """
        # 保存するデータの構築
        data = {
            "user_id": user_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "advice": advice,
            "created_at": datetime.now()
        }
        
        # Firestoreに保存
        doc_ref = self.db.collection("users").document(user_id)\
            .collection("analysis_history").document()
        doc_ref.set(data)
        
        return doc_ref.id
        
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ユーザーの解析履歴を取得
        
        Args:
            user_id: ユーザーID
            limit: 取得する履歴の最大数
            
        Returns:
            List[Dict]: 解析履歴のリスト（新しい順）
        """
        # 履歴を取得（created_atの降順）
        docs = self.db.collection("users").document(user_id)\
            .collection("analysis_history")\
            .order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .stream()
            
        # ドキュメントをリストに変換
        history = []
        for doc in docs:
            data = doc.to_dict()
            # datetime型をISO形式の文字列に変換
            data["created_at"] = data["created_at"].isoformat()
            data["id"] = doc.id
            history.append(data)
            
        return history 