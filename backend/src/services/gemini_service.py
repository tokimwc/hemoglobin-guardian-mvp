from google.cloud import aiplatform
from typing import Optional, List, Dict
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

@dataclass
class NutritionAdvice:
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: List[str]

class GeminiService:
    def __init__(self):
        self.client = aiplatform.gapic.PredictionServiceClient(
            client_options={"api_endpoint": "asia-northeast1-aiplatform.googleapis.com"}
        )
        self._executor = ThreadPoolExecutor()
        
    async def generate_advice(
        self,
        risk_level: str,
        confidence_score: float,
        warnings: List[str]
    ) -> NutritionAdvice:
        """
        リスクレベルに応じた栄養アドバイスを生成
        
        Args:
            risk_level: "LOW", "MEDIUM", "HIGH"のいずれか
            confidence_score: 解析結果の信頼度（0-1）
            warnings: 画像品質に関する警告メッセージのリスト
            
        Returns:
            NutritionAdvice: 構造化された栄養アドバイス
        """
        # プロンプトの構築
        prompt = self._create_prompt(risk_level, confidence_score, warnings)
        
        try:
            # Gemini APIを非同期で呼び出してアドバイスを生成
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self._executor,
                self._call_gemini_api,
                prompt
            )
            return self._format_response(response, risk_level, warnings)
        except Exception as e:
            # エラー時のフォールバック
            return self._get_fallback_advice(risk_level, str(e))

    def _create_prompt(
        self,
        risk_level: str,
        confidence_score: float,
        warnings: List[str]
    ) -> str:
        """プロンプトを生成"""
        base_context = """
        あなたは貧血予防の専門家です。
        ユーザーの爪の色解析結果に基づいて、具体的な栄養アドバイスを提供してください。
        
        以下の形式でJSONレスポンスを生成してください：
        {
            "summary": "全体的なアドバイスの要約（100文字程度）",
            "iron_rich_foods": ["鉄分が豊富な食材のリスト"],
            "meal_suggestions": ["具体的な食事メニューの提案"],
            "lifestyle_tips": ["生活習慣に関するアドバイス"]
        }
        
        アドバイスは以下の点を考慮してください：
        - 鉄分の吸収を促進する食材の組み合わせ
        - 季節や入手のしやすさ
        - 調理の手軽さ
        - 日本の食文化との親和性
        """
        
        risk_contexts = {
            "LOW": "貧血リスクは低めですが、予防的なアドバイスを提供してください。",
            "MEDIUM": "貧血リスクは中程度です。積極的な改善アドバイスを提供してください。",
            "HIGH": "貧血リスクは高めです。具体的で実行しやすい改善アドバイスを提供してください。"
        }
        
        confidence_context = f"\n解析の信頼度は{confidence_score:.1%}です。"
        warnings_context = "\n".join([f"注意: {w}" for w in warnings]) if warnings else ""
        
        return f"{base_context}\n{risk_contexts.get(risk_level, risk_contexts['MEDIUM'])}{confidence_context}\n{warnings_context}"

    def _call_gemini_api(self, prompt: str) -> str:
        """Gemini APIを呼び出してレスポンスを取得"""
        # TODO: 実際のGemini API呼び出し実装
        # 現在はモックレスポンスを返す
        mock_responses = {
            "LOW": {
                "summary": "予防的な観点から、日々の食事で鉄分を意識的に摂取することをおすすめします。",
                "iron_rich_foods": ["ほうれん草", "レバー", "牡蠣", "枝豆", "ひじき"],
                "meal_suggestions": [
                    "ほうれん草と豆腐の炒め物",
                    "レバーの甘辛煮",
                    "ひじきの煮物"
                ],
                "lifestyle_tips": [
                    "食事は規則正しく取りましょう",
                    "緑茶は鉄分の吸収を妨げるので、食事の直後は避けましょう"
                ]
            }
        }
        return json.dumps(mock_responses.get("LOW"))

    def _format_response(
        self,
        response: str,
        risk_level: str,
        warnings: List[str]
    ) -> NutritionAdvice:
        """APIレスポンスを整形"""
        try:
            data = json.loads(response)
            return NutritionAdvice(
                summary=data["summary"],
                iron_rich_foods=data["iron_rich_foods"],
                meal_suggestions=data["meal_suggestions"],
                lifestyle_tips=data["lifestyle_tips"],
                warnings=warnings
            )
        except (json.JSONDecodeError, KeyError) as e:
            return self._get_fallback_advice(risk_level, str(e))

    def _get_fallback_advice(self, risk_level: str, error: str) -> NutritionAdvice:
        """エラー時のフォールバックアドバイス"""
        return NutritionAdvice(
            summary="申し訳ありません。アドバイス生成中にエラーが発生しました。一般的な貧血予防のアドバイスを提供させていただきます。",
            iron_rich_foods=["レバー", "ほうれん草", "牡蠣"],
            meal_suggestions=["レバーとほうれん草の炒め物"],
            lifestyle_tips=["規則正しい食事を心がけましょう"],
            warnings=[f"アドバイス生成エラー: {error}"]
        ) 