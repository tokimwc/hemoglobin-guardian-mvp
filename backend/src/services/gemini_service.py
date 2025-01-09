from google.cloud import aiplatform
from typing import Optional
import json

class GeminiService:
    def __init__(self):
        self.client = aiplatform.gapic.PredictionServiceClient(
            client_options={"api_endpoint": "asia-northeast1-aiplatform.googleapis.com"}
        )
        
    def generate_advice(self, risk_level: str) -> str:
        """
        リスクレベルに応じた栄養アドバイスを生成
        
        Args:
            risk_level: "LOW", "MEDIUM", "HIGH"のいずれか
            
        Returns:
            str: 生成されたアドバイス文
        """
        # プロンプトの構築
        prompt = self._create_prompt(risk_level)
        
        try:
            # Gemini APIを呼び出してアドバイスを生成
            response = self._call_gemini_api(prompt)
            return self._format_response(response)
        except Exception as e:
            return f"申し訳ありません。アドバイス生成中にエラーが発生しました: {str(e)}"

    def _create_prompt(self, risk_level: str) -> str:
        """プロンプトを生成"""
        base_context = """
        あなたは貧血予防の専門家です。
        ユーザーの爪の色解析結果に基づいて、具体的な栄養アドバイスを提供してください。
        アドバイスは以下の点を含めてください：
        - 鉄分を効率的に摂取できる食材
        - 具体的な食事例
        - 生活習慣のアドバイス
        
        回答は150文字程度で、親しみやすい口調でお願いします。
        """
        
        risk_contexts = {
            "LOW": f"貧血リスクは{risk_level}（低め）ですが、予防的なアドバイスをお願いします。",
            "MEDIUM": f"貧血リスクは{risk_level}（中程度）です。改善のためのアドバイスをお願いします。",
            "HIGH": f"貧血リスクは{risk_level}（高め）です。具体的な改善アドバイスをお願いします。"
        }
        
        return f"{base_context}\n{risk_contexts.get(risk_level, risk_contexts['MEDIUM'])}"

    def _call_gemini_api(self, prompt: str) -> str:
        """Gemini APIを呼び出してレスポンスを取得"""
        # TODO: 実際のGemini API呼び出し実装
        # 現在はモックレスポンスを返す
        mock_responses = {
            "LOW": "予防的な観点から、普段の食事に鉄分を意識的に取り入れましょう。ほうれん草と豆腐の炒め物や、レバーの甘辛煮など、美味しく鉄分を摂取できるメニューがおすすめです。",
            "MEDIUM": "鉄分の吸収を高めるため、ビタミンCを含む食材と組み合わせましょう。例えば、ほうれん草のお浸しにレモン果汁を加えたり、レバーニラ炒めにトマトを添えるのがおすすめです。",
            "HIGH": "積極的な鉄分摂取が必要です。レバー、牡蠣、ほうれん草などの鉄分豊富な食材を毎日の食事に取り入れましょう。特に、レバーとほうれん草の炒め物は鉄分とビタミンCを同時に摂取できるのでおすすめです。"
        }
        return mock_responses.get("MEDIUM")  # デフォルトは MEDIUM のレスポンス

    def _format_response(self, response: str) -> str:
        """APIレスポンスを整形"""
        return response.strip() 