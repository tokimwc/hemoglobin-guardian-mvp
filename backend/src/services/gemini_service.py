from google.cloud import aiplatform
from typing import Optional, List, Dict, Union
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
import os
from dotenv import load_dotenv
from functools import lru_cache
import time
import hashlib

# 環境変数の読み込み
load_dotenv()

@dataclass(frozen=True)
class CacheKey:
    """キャッシュのキーとして使用するデータクラス"""
    risk_level: str
    warnings_hash: str
    
    @classmethod
    def create(cls, risk_level: str, warnings: List[str]) -> 'CacheKey':
        """警告リストのハッシュ値を含むキーを生成"""
        warnings_str = ','.join(sorted(warnings)) if warnings else ''
        warnings_hash = hashlib.md5(warnings_str.encode()).hexdigest()
        return cls(risk_level=risk_level, warnings_hash=warnings_hash)

@dataclass
class BaseResponse:
    """レスポンスの基底クラス"""
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: List[str]
    timestamp: float = time.time()
    cached: bool = False

@dataclass
class NutritionAdvice(BaseResponse):
    """栄養アドバイスのレスポンスクラス"""
    pass

@dataclass
class ErrorResponse(BaseResponse):
    """エラー時のレスポンスクラス"""
    error_type: str = "SYSTEM_ERROR"

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
        
        # キャッシュとタイムアウトの設定
        self._advice_cache: Dict[CacheKey, NutritionAdvice] = {}
        self._error_cache = {}
        self._timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "4.0"))
        self._cache_ttl = int(os.getenv("ADVICE_CACHE_TTL_SECONDS", "3600"))  # 1時間
        self._last_cache_cleanup = time.time()

    def _cleanup_cache(self):
        """期限切れのキャッシュエントリを削除"""
        current_time = time.time()
        if current_time - self._last_cache_cleanup > 300:  # 5分ごとにクリーンアップ
            expired_keys = [
                key for key, value in self._advice_cache.items()
                if current_time - value.timestamp > self._cache_ttl
            ]
            for key in expired_keys:
                del self._advice_cache[key]
            self._last_cache_cleanup = current_time

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
    ) -> Union[NutritionAdvice, ErrorResponse]:
        """アドバイスを生成（キャッシュがある場合はそれを使用）"""
        try:
            # 入力値の検証
            if risk_level not in ["LOW", "MEDIUM", "HIGH"]:
                raise ValueError(f"無効なリスクレベル: {risk_level}")
            if not 0 <= confidence_score <= 1.0:
                raise ValueError(f"無効な信頼度スコア: {confidence_score}")

            # キャッシュキーの生成
            cache_key = CacheKey.create(risk_level, warnings)
            
            # キャッシュのクリーンアップ
            self._cleanup_cache()
            
            # キャッシュチェック
            if cache_key in self._advice_cache:
                cached_advice = self._advice_cache[cache_key]
                if time.time() - cached_advice.timestamp < self._cache_ttl:
                    return NutritionAdvice(
                        summary=cached_advice.summary,
                        iron_rich_foods=cached_advice.iron_rich_foods,
                        meal_suggestions=cached_advice.meal_suggestions,
                        lifestyle_tips=cached_advice.lifestyle_tips,
                        warnings=cached_advice.warnings,
                        cached=True
                    )

            # 新しいアドバイスを生成
            advice = await self._execute_with_timeout(
                self._generate_advice_internal(risk_level, confidence_score, warnings),
                timeout=self._timeout_seconds
            )
            
            # キャッシュに保存
            if isinstance(advice, NutritionAdvice):  # エラーレスポンスでない場合のみキャッシュ
                self._advice_cache[cache_key] = advice
            
            return advice

        except Exception as e:
            return await self._create_error_response(str(e))

    async def _execute_with_timeout(self, coroutine, timeout: float):
        try:
            return await asyncio.wait_for(coroutine, timeout=timeout)
        except asyncio.TimeoutError:
            return await self._create_timeout_response()

    @lru_cache(maxsize=100)
    def _create_error_response_data(self, error_type: str = "SYSTEM_ERROR") -> ErrorResponse:
        """エラーレスポンスのデータを生成（同期メソッド）"""
        return ErrorResponse(
            summary="システムエラーが発生しました。一時的な問題の可能性があります。",
            warnings=[f"エラーが発生しました: {error_type}"],
            iron_rich_foods=[
                "レバー（豚、鶏、牛）",
                "赤身の魚（マグロ、カツオ）",
                "ほうれん草",
                "大豆製品"
            ],
            meal_suggestions=[
                "バランスの取れた食事を心がけてください",
                "鉄分を多く含む食材を取り入れましょう"
            ],
            lifestyle_tips=[
                "定期的な運動を心がけましょう",
                "十分な睡眠を取りましょう",
                "医師に相談することをお勧めします"
            ],
            error_type=error_type
        )

    async def _create_error_response(self, error_type: str = "SYSTEM_ERROR") -> ErrorResponse:
        """エラーレスポンスを非同期で生成"""
        return self._create_error_response_data(error_type)

    async def _create_timeout_response(self) -> ErrorResponse:
        """タイムアウト時のエラーレスポンスを生成"""
        return self._create_error_response_data("TIMEOUT_ERROR: 応答時間が制限を超えました")

    async def _generate_advice_internal(
        self,
        risk_level: str,
        confidence_score: float,
        warnings: List[str]
    ) -> Union[NutritionAdvice, ErrorResponse]:
        """アドバイスを内部的に生成"""
        try:
            # プロンプトの構築
            prompt = self._create_prompt(risk_level, confidence_score, warnings)
            
            # Gemini APIを非同期で呼び出してアドバイスを生成
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self._executor,
                self._call_gemini_api,
                prompt
            )
            
            # レスポンスをパース
            try:
                data = json.loads(response)
                return NutritionAdvice(
                    summary=data["summary"],
                    iron_rich_foods=data["iron_rich_foods"],
                    meal_suggestions=data["meal_suggestions"],
                    lifestyle_tips=data["lifestyle_tips"],
                    warnings=warnings
                )
            except json.JSONDecodeError as e:
                return await self._create_error_response(f"JSONDecodeError: {str(e)}")
            except KeyError as e:
                return await self._create_error_response(f"KeyError: {str(e)}")
        except Exception as e:
            return await self._create_error_response(str(e))

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
            "iron_rich_foods": ["鉄分が豊富な食材のリスト（5-7項目）"],
            "meal_suggestions": ["具体的な食事メニューの提案（3-5項目）"],
            "lifestyle_tips": ["生活習慣に関するアドバイス（3-5項目）"]
        }
        
        アドバイスは以下の点を考慮してください：
        1. 鉄分の吸収を促進する食材の組み合わせ
           - ビタミンCとの組み合わせ
           - タンニンを含む飲み物は避ける
        2. 季節性と入手のしやすさ
           - 旬の食材を優先
           - スーパーで一般的に手に入る食材
        3. 調理の手軽さ
           - 15-30分程度で作れるメニュー
           - 特別な調理器具を必要としない
        4. 日本の食文化との親和性
           - 和食中心のメニュー
           - 日常的に取り入れやすい食材
        """
        
        risk_text = {
            "LOW": f"貧血リスクは低めです（{risk_level}）",
            "MEDIUM": f"貧血リスクは中程度です（{risk_level}）",
            "HIGH": f"貧血リスクは高めです（{risk_level}）"
        }.get(risk_level, f"貧血リスクは中程度です（MEDIUM）")
        
        confidence_text = f"（信頼度: {int(confidence_score * 100)}%）"
        warnings_text = "注意事項:\n" + "\n".join(warnings) if warnings else ""
        
        return f"{base_context}\n\n状況:\n{risk_text}{confidence_text}\n{warnings_text}" 