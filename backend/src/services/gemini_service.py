from google.cloud import aiplatform
from typing import Optional, List, Dict
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

@dataclass
class NutritionAdvice:
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: List[str]

class GeminiService:
    def __init__(self):
        # 環境変数の取得
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        model_id = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-pro")
        
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
            
        # Vertex AIの初期化
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(model_id)
        self._executor = ThreadPoolExecutor()
        
        # API設定の読み込み
        self.temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", "1024"))
        self.top_p = float(os.getenv("GEMINI_TOP_P", "0.8"))
        self.top_k = int(os.getenv("GEMINI_TOP_K", "40"))

    def _call_gemini_api(self, prompt: str) -> str:
        """Gemini APIを呼び出してレスポンスを取得"""
        try:
            # 生成パラメータの設定
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=self.top_p,
                top_k=self.top_k
            )
            
            # Gemini APIを呼び出し
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # レスポンスをパースしてJSONとして返す
            try:
                # 生のテキストを取得
                text = response.text
                # 余分な空白や改行を削除
                text = text.strip()
                # コードブロックを削除（もし存在する場合）
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                
                json_response = json.loads(text)
                return json.dumps(json_response)
            except json.JSONDecodeError as e:
                # JSONパースに失敗した場合は、エラーを発生させてフォールバックを使用
                raise ValueError(f"JSONDecodeError: Invalid JSON response from Gemini API. Error: {str(e)}, Response: {text}")
                
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")

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

        重要: リスクレベルに応じて、以下のキーワードを必ずsummaryに含めてください：
        - LOWの場合：「予防」というキーワードを含める
        - MEDIUMの場合：「可能性」というキーワードを含める
        - HIGHの場合：「改善」または「対策」というキーワードを含める
        """
        
        risk_contexts = {
            "LOW": "貧血リスクは低めです（LOW）。予防的な観点から、貧血を防ぐためのアドバイスを提供してください。",
            "MEDIUM": "貧血リスクは中程度です（MEDIUM）。貧血の可能性を考慮した積極的な改善アドバイスを提供してください。",
            "HIGH": "貧血リスクは高めです（HIGH）。早急な改善が必要です。具体的な対策と実行しやすい改善アドバイスを提供してください。"
        }
        
        confidence_context = f"\n解析の信頼度は{confidence_score:.0%}です。"
        warnings_context = "\n".join([f"注意: {w}" for w in warnings]) if warnings else ""
        
        return f"{base_context}\n{risk_contexts.get(risk_level, risk_contexts['MEDIUM'])}{confidence_context}\n{warnings_context}"

    def _format_response(
        self,
        response: str,
        risk_level: str,
        warnings: List[str]
    ) -> NutritionAdvice:
        """APIレスポンスを整形"""
        try:
            data = json.loads(response)
            # 既存の警告に新しい警告を追加
            all_warnings = warnings.copy()
            return NutritionAdvice(
                summary=data["summary"],
                iron_rich_foods=data["iron_rich_foods"],
                meal_suggestions=data["meal_suggestions"],
                lifestyle_tips=data["lifestyle_tips"],
                warnings=all_warnings
            )
        except json.JSONDecodeError as e:
            return self._get_fallback_advice(risk_level, f"JSONDecodeError: レスポンスの解析に失敗しました - {str(e)}", warnings)
        except KeyError as e:
            return self._get_fallback_advice(risk_level, f"KeyError: 必要なキー {str(e)} が見つかりません", warnings)

    def _get_fallback_advice(self, risk_level: str, error: str, warnings: List[str] = None) -> NutritionAdvice:
        """エラー時のフォールバックアドバイス"""
        all_warnings = warnings.copy() if warnings else []
        all_warnings.append(f"アドバイス生成エラー: {error}")
        
        return NutritionAdvice(
            summary="申し訳ありません。アドバイス生成中にエラーが発生しました。一般的な貧血予防のアドバイスを提供させていただきます。",
            iron_rich_foods=["レバー", "ほうれん草", "牡蠣"],
            meal_suggestions=["レバーとほうれん草の炒め物"],
            lifestyle_tips=["規則正しい食事を心がけましょう"],
            warnings=all_warnings
        ) 