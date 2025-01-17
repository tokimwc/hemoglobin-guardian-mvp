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

@dataclass(frozen=True)
class ErrorResponse:
    summary: str
    warnings: List[str]
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    timestamp: float = time.time()

@dataclass
class NutritionAdvice:
    summary: str
    iron_rich_foods: List[str]
    meal_suggestions: List[str]
    lifestyle_tips: List[str]
    warnings: List[str]
    cached: bool = False

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

    async def generate_advice(self, risk_level: str, confidence_score: float, warnings: List[str]) -> NutritionAdvice:
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
                        **{k: v for k, v in cached_advice.__dict__.items() if k != 'timestamp'},
                        cached=True
                    )

            # 新しいアドバイスを生成
            advice = await self._execute_with_timeout(
                self._generate_advice_internal(risk_level, confidence_score, warnings),
                timeout=self._timeout_seconds
            )
            
            # キャッシュに保存
            if isinstance(advice, NutritionAdvice):  # エラーレスポンスでない場合のみキャッシュ
                advice.timestamp = time.time()
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
            summary="申し訳ありません。システムエラーが発生しました。一時的な問題の可能性があります。",
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
            ]
        )

    async def _create_error_response(self, error_type: str = "SYSTEM_ERROR") -> ErrorResponse:
        """エラーレスポンスを非同期で生成"""
        return self._create_error_response_data(error_type)

    async def _create_timeout_response(self) -> ErrorResponse:
        """タイムアウト時のエラーレスポンスを生成"""
        return self._create_error_response_data("TIMEOUT_ERROR: 応答時間が制限を超えました")

    async def _generate_advice_internal(self, risk_level: str, confidence_score: float, warnings: List[str]):
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

        重要: リスクレベルに応じて、以下のキーワードを必ずsummaryに含めてください：
        - LOWの場合：「予防」というキーワードを含める
        - MEDIUMの場合：「可能性」というキーワードを含める
        - HIGHの場合：「改善」または「対策」というキーワードを含める
        """
        
        risk_contexts = {
            "LOW": """
            貧血リスクは低めです（LOW）。
            予防的な観点から、以下の点を考慮したアドバイスを提供してください：
            - 現状維持のための具体的な食事プラン
            - 手軽に継続できる予防的な習慣
            - 鉄分を日常的に補給できる食材選び
            """,
            "MEDIUM": """
            貧血リスクは中程度です（MEDIUM）。
            貧血の可能性を考慮し、以下の点を重視したアドバイスを提供してください：
            - 鉄分摂取を増やすための具体的な食事改善案
            - 1週間の食事プランの例
            - 生活習慣の見直しポイント
            """,
            "HIGH": """
            貧血リスクは高めです（HIGH）。
            早急な改善が必要です。以下の点を含む具体的なアドバイスを提供してください：
            - すぐに実践できる食事の改善対策
            - 鉄分を効率的に摂取できる食材と調理法
            - 医師への相談を推奨する具体的な症状の説明
            """
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
        
        # リスクレベルに応じたフォールバックメッセージ
        risk_messages = {
            "LOW": {
                "summary": "貧血の予防のため、日々の食事で鉄分を意識的に摂取することをお勧めします。システムエラーが発生しましたが、一般的な予防アドバイスをご提供します。",
                "iron_rich_foods": [
                    "ほうれん草（和食の定番）",
                    "レバー（豚、鶏、牛）",
                    "牡蠣（生食や加熱）",
                    "大豆製品（納豆、豆腐）",
                    "ひじき（乾物）"
                ],
                "meal_suggestions": [
                    "ほうれん草と油揚げの煮浸し",
                    "レバニラ炒め",
                    "ひじきの煮物"
                ],
                "lifestyle_tips": [
                    "毎食、野菜を1/3程度取り入れましょう",
                    "ビタミンCを含む果物を食後に摂取すると鉄分の吸収が良くなります",
                    "定期的な運動で血行を促進しましょう"
                ]
            },
            "MEDIUM": {
                "summary": "貧血の可能性があるため、積極的な鉄分摂取をお勧めします。システムエラーが発生しましたが、一般的な改善アドバイスをご提供します。",
                "iron_rich_foods": [
                    "レバー（鉄分が特に豊富）",
                    "赤身肉（牛肉、豚肉）",
                    "ほうれん草（和食に取り入れやすい）",
                    "小松菜（手に入りやすい）",
                    "納豆（毎日の食事に）",
                    "あさり（味噌汁の具に）"
                ],
                "meal_suggestions": [
                    "レバーの甘辛炒め（ビタミンC野菜を添えて）",
                    "小松菜と油揚げの煮浸し",
                    "あさりの味噌汁と納豆ご飯",
                    "牛肉と青菜の炒め物"
                ],
                "lifestyle_tips": [
                    "鉄分の多い食材を毎食1品以上取り入れましょう",
                    "コーヒーや緑茶は食事の30分以上前後を空けて飲みましょう",
                    "十分な睡眠を取り、ストレスを軽減しましょう",
                    "定期的な血液検査をお勧めします"
                ]
            },
            "HIGH": {
                "summary": "貧血リスクが高いため、早急な対策が必要です。システムエラーが発生しましたが、重要な改善アドバイスをご提供します。医師への相談も推奨します。",
                "iron_rich_foods": [
                    "レバー（豚、鶏、牛：鉄分が極めて豊富）",
                    "牡蠣（生食や加熱調理）",
                    "赤身肉（牛肉が特におすすめ）",
                    "ほうれん草（毎日の食事に）",
                    "小松菜（手に入りやすい）",
                    "ひじき（乾物で常備に）",
                    "あさり（味噌汁やパスタに）"
                ],
                "meal_suggestions": [
                    "レバーの生姜焼き（ビタミンC野菜を多めに）",
                    "牡蠣と小松菜の炒め物",
                    "ひじきと大豆の煮物",
                    "牛肉とほうれん草のソテー",
                    "あさりと青菜の和風パスタ"
                ],
                "lifestyle_tips": [
                    "できるだけ早めに医師に相談することをお勧めします",
                    "鉄分サプリメントの使用を医師に相談してみましょう",
                    "毎食、鉄分の多い食材を必ず取り入れましょう",
                    "ビタミンCを含む食材と組み合わせて摂取しましょう",
                    "十分な休息を取り、無理な運動は控えめにしましょう"
                ]
            }
        }
        
        # デフォルトはMEDIUMのメッセージを使用
        fallback = risk_messages.get(risk_level, risk_messages["MEDIUM"])
        
        return NutritionAdvice(
            summary=fallback["summary"],
            iron_rich_foods=fallback["iron_rich_foods"],
            meal_suggestions=fallback["meal_suggestions"],
            lifestyle_tips=fallback["lifestyle_tips"],
            warnings=all_warnings
        ) 