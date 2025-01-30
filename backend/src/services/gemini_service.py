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
import logging
from src.models.error_response import ErrorResponse
from src.models.nutrition_advice import NutritionAdvice
from asyncio import Lock, Semaphore
from datetime import datetime, timedelta

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

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
    """Gemini APIを使用したアドバイス生成サービス"""
    
    def __init__(self, project_id: str, location: str):
        """
        GeminiServiceの初期化
        Args:
            project_id (str): Google Cloud プロジェクトID
            location (str): Vertex AI のロケーション
        """
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.0-pro")
        self._executor = ThreadPoolExecutor()
        self._advice_cache: Dict[CacheKey, NutritionAdvice] = {}
        self._cache_lock = Lock()
        self._cache_ttl = 300  # 5分
        self._last_cache_cleanup = time.time()
        self._cleanup_interval = 60  # 1分
        self._request_semaphore = Semaphore(10)
        
        # 生成パラメータの設定
        self.temperature = 0.7
        self.max_tokens = 1024
        self.top_p = 0.8
        self.top_k = 40

    async def generate_advice(self, analysis_result: Dict) -> Union[NutritionAdvice, ErrorResponse]:
        """リスクレベルの検証を強化"""
        try:
            # リスクレベルの検証
            raw_risk_level = analysis_result.get("risk_level")
            if raw_risk_level is None:
                logger.warning("リスクレベルが指定されていません")
                return ErrorResponse(
                    summary="リスクレベルが見つかりません",
                    warnings=["リスクレベルが含まれていません"],
                    iron_rich_foods=["ほうれん草", "レバー", "牛肉"],
                    meal_suggestions=["鉄分豊富な食事を心がけましょう"],
                    lifestyle_tips=["十分な睡眠をとりましょう"],
                    error_type="VALIDATION_ERROR"
                )

            risk_level = str(raw_risk_level).lower()
            if risk_level not in ["low", "medium", "high"]:
                logger.warning(f"無効なリスクレベル: {risk_level}")
                return ErrorResponse(
                    summary="無効なリスクレベルが指定されました",
                    warnings=[f"リスクレベル '{risk_level}' は無効です"],
                    iron_rich_foods=["ほうれん草", "レバー", "牛肉"],
                    meal_suggestions=["鉄分豊富な食事を心がけましょう"],
                    lifestyle_tips=["十分な睡眠をとりましょう"],
                    error_type="VALIDATION_ERROR"
                )

            confidence_score = analysis_result.get("confidence_score", 0.0)
            warnings = analysis_result.get("warnings", [])
            
            # キャッシュチェック
            cache_key = CacheKey.create(risk_level, warnings)
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                logger.debug("キャッシュからレスポンスを返却")
                return cached_response

            async with self._request_semaphore:
                try:
                    response = await self._generate_advice_internal(
                        risk_level,
                        confidence_score,
                        warnings
                    )
                    if isinstance(response, NutritionAdvice):
                        await self._save_to_cache(cache_key, response)
                    return response
                except Exception as e:
                    logger.error(f"アドバイス生成中にエラー: {str(e)}")
                    return self._create_error_response_data(
                        "アドバイス生成中にエラーが発生しました",
                        "GENERATION_ERROR"
                    )

        except Exception as e:
            logger.error(f"予期せぬエラー: {str(e)}")
            return self._create_error_response_data(
                "システムエラーが発生しました",
                "SYSTEM_ERROR"
            )

    async def generate_advice_async(
        self,
        analysis_result: Dict,
        confidence_score: Optional[float] = None,
        warnings: Optional[List[str]] = None
    ) -> Union[NutritionAdvice, ErrorResponse]:
        """
        generate_adviceのエイリアス（後方互換性のため）
        """
        return await self.generate_advice(
            analysis_result,
            confidence_score=confidence_score,
            warnings=warnings
        )

    def _create_prompt(self, risk_level: str, confidence: float, warnings: List[str]) -> str:
        """
        Geminiへのプロンプトを生成
        Args:
            risk_level (str): リスクレベル
            confidence (float): 信頼度スコア
            warnings (List[str]): 警告メッセージのリスト
        Returns:
            str: 生成されたプロンプト
        """
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
            "low": "貧血リスクは低めです",
            "medium": "貧血リスクは中程度です",
            "high": "貧血リスクは高めです"
        }.get(risk_level.lower(), "貧血リスクは中程度です")
        
        confidence_text = f"（信頼度: {int(confidence * 100)}%）"
        warnings_text = "注意事項:\n" + "\n".join(warnings) if warnings else ""
        
        return f"{base_context}\n\n状況:\n{risk_text}{confidence_text}\n{warnings_text}"

    def _parse_response(self, response_text: str) -> Dict:
        """
        Geminiからのレスポンスをパース
        Args:
            response_text (str): Geminiからのレスポンステキスト
        Returns:
            Dict: パースされたレスポンス
        """
        try:
            # レスポンステキストからJSONブロックを抽出
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            json_str = response_text[start_idx:end_idx]
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"レスポンスのパースに失敗: {str(e)}")
            raise ValueError(f"Geminiからのレスポンスのパースに失敗しました: {str(e)}")

    async def _cleanup_cache(self):
        """期限切れのキャッシュエントリを削除（スレッドセーフ）"""
        current_time = time.time()
        
        if current_time - self._last_cache_cleanup < self._cleanup_interval:
            return
            
        async with self._cache_lock:
            try:
                expired_keys = [
                    key for key, value in self._advice_cache.items()
                    if current_time - value.timestamp > self._cache_ttl
                ]
                
                for key in expired_keys:
                    del self._advice_cache[key]
                    
                self._last_cache_cleanup = current_time
                
                if expired_keys:
                    logger.info(f"キャッシュクリーンアップ完了: {len(expired_keys)}件のエントリを削除")
                    
            except Exception as e:
                logger.error(f"キャッシュクリーンアップ中にエラー: {str(e)}")

    async def _get_from_cache(self, cache_key: CacheKey) -> Optional[NutritionAdvice]:
        """キャッシュからアドバイスを取得（スレッドセーフ）"""
        async with self._cache_lock:
            if cache_key in self._advice_cache:
                advice = self._advice_cache[cache_key]
                if time.time() - advice.timestamp <= self._cache_ttl:
                    return advice
                else:
                    del self._advice_cache[cache_key]
        return None

    async def _save_to_cache(self, cache_key: CacheKey, advice: NutritionAdvice):
        """キャッシュにアドバイスを保存（スレッドセーフ）"""
        async with self._cache_lock:
            self._advice_cache[cache_key] = advice
            
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
            logger.debug(f"生成されたプロンプト: {prompt}")
            
            # Gemini APIを非同期で呼び出してアドバイスを生成
            response = await self._call_gemini_api(prompt)
            logger.debug(f"Gemini APIレスポンス: {response}")
            
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
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"レスポンスのパースに失敗: {str(e)}, レスポンス: {response}")
                return ErrorResponse(
                    summary="レスポンスの解析に失敗しました",
                    warnings=[f"パースエラー: {str(e)}"],
                    iron_rich_foods=["ほうれん草", "レバー", "牛肉"],
                    meal_suggestions=["鉄分豊富な食事を心がけましょう"],
                    lifestyle_tips=["十分な睡眠をとりましょう"],
                    error_type="PARSE_ERROR"
                )
        except Exception as e:
            logger.error(f"アドバイス生成中にエラー: {str(e)}")
            return ErrorResponse(
                summary="アドバイス生成中にエラーが発生しました",
                warnings=[str(e)],
                iron_rich_foods=["ほうれん草", "レバー", "牛肉"],
                meal_suggestions=["鉄分豊富な食事を心がけましょう"],
                lifestyle_tips=["十分な睡眠をとりましょう"],
                error_type="GENERATION_ERROR"
            )

    async def _call_gemini_api(self, prompt: str) -> str:
        """Gemini APIを非同期で呼び出してレスポンスを取得"""
        try:
            # 生成パラメータの設定
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=self.top_p,
                top_k=self.top_k
            )
            
            # Gemini APIを非同期で呼び出し
            response = await self.model.generate_content(
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
                
                # JSONとして解析できることを確認
                json.loads(text)  # バリデーションのみ
                return text
                
            except json.JSONDecodeError as e:
                raise ValueError(f"JSONDecodeError: Invalid JSON response from Gemini API. Error: {str(e)}, Response: {text}")
                
        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")

    @lru_cache(maxsize=100)
    def _create_error_response_data(self, error_message: str, error_type: str = "SYSTEM_ERROR") -> ErrorResponse:
        """エラーレスポンスのデータを生成（同期メソッド）"""
        return ErrorResponse(
            summary=error_message,
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
        return self._create_error_response_data("システムエラーが発生しました。一時的な問題の可能性があります。", error_type)

    async def _create_timeout_response(self) -> ErrorResponse:
        """タイムアウト時のエラーレスポンスを生成"""
        return self._create_error_response_data(
            "応答時間が制限を超えました",
            "TIMEOUT_ERROR"
        ) 