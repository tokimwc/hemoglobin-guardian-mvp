from google.cloud import vision
from typing import List, Tuple, Dict, Optional
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from dataclasses import dataclass
import os

@dataclass
class ImageQualityMetrics:
    is_blurry: bool
    brightness_score: float
    has_proper_lighting: bool
    has_detected_nail: bool

@dataclass
class NailAnalysisResult:
    risk_score: float
    quality_metrics: ImageQualityMetrics
    detected_colors: List[Dict]
    confidence_score: float

class VisionService:
    """Vision AIを使用した画像解析サービス"""
    
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
    
    def analyze_image(self, image_content: bytes) -> Dict:
        """画像を解析し、色情報などを取得する"""
        try:
            image = vision.Image(content=image_content)
            
            # 画像プロパティの解析
            response = self.client.image_properties(image=image)
            props = response.image_properties_annotation
            
            # 色情報の抽出
            colors = []
            for color in props.dominant_colors.colors:
                colors.append({
                    'red': color.color.red,
                    'green': color.color.green,
                    'blue': color.color.blue,
                    'score': color.score,
                    'pixel_fraction': color.pixel_fraction
                })
            
            return {
                'color_properties': colors,
                'error': None
            }
            
        except Exception as e:
            raise Exception(f"画像の解析に失敗しました: {str(e)}")

    async def analyze_image_async(self, image_content: bytes) -> NailAnalysisResult:
        """
        画像を非同期で解析し、貧血リスクスコアを算出
        
        Args:
            image_content: 画像のバイトデータ
            
        Returns:
            NailAnalysisResult: 解析結果を含むオブジェクト
        """
        image = vision.Image(content=image_content)
        
        async def _run_analysis():
            # 並列で複数の解析を実行
            loop = asyncio.get_event_loop()
            properties_future = loop.run_in_executor(
                self._executor,
                self.client.image_properties,
                image
            )
            object_future = loop.run_in_executor(
                self._executor,
                self.client.object_localization,
                image
            )
            face_future = loop.run_in_executor(
                self._executor,
                self.client.face_detection,
                image
            )
            
            # 結果を待機
            properties = await properties_future
            objects = await object_future
            faces = await face_future
            
            return properties, objects, faces
        
        # 解析の実行
        properties, objects, faces = await _run_analysis()
        
        # 画質チェック
        quality_metrics = self._check_image_quality(properties.image_properties_annotation)
        
        # 爪の検出確認
        quality_metrics.has_detected_nail = self._detect_nail_region(objects.localized_object_annotations)
        
        # 色解析とリスクスコア計算
        colors, risk_score = self._analyze_colors(properties.image_properties_annotation)
        
        # 信頼度スコアの計算
        confidence = self._calculate_confidence_score(quality_metrics, objects.localized_object_annotations)
        
        return NailAnalysisResult(
            risk_score=risk_score,
            quality_metrics=quality_metrics,
            detected_colors=colors,
            confidence_score=confidence
        )

    def _check_image_quality(self, properties) -> ImageQualityMetrics:
        """画像品質のチェック"""
        # 明るさスコアの計算
        brightness = sum(
            color.color.red + color.color.green + color.color.blue
            for color in properties.dominant_colors.colors
        ) / (len(properties.dominant_colors.colors) * 3)
        
        # 適切な照明条件かチェック
        proper_lighting = 0.3 <= brightness <= 0.8
        
        # ブレ検出（色の鮮明さで判定）
        is_blurry = any(
            color.score < 0.1 for color in properties.dominant_colors.colors
        )
        
        return ImageQualityMetrics(
            is_blurry=is_blurry,
            brightness_score=brightness,
            has_proper_lighting=proper_lighting,
            has_detected_nail=False  # 後で更新
        )

    def _detect_nail_region(self, objects) -> bool:
        """爪領域の検出"""
        # 手や指のオブジェクトを探す
        relevant_labels = {'Hand', 'Finger', 'Nail'}
        detected_objects = {obj.name for obj in objects}
        return bool(detected_objects & relevant_labels)

    def _analyze_colors(self, properties) -> Tuple[List[Dict], float]:
        """色解析とリスクスコア計算"""
        colors = []
        for color in properties.dominant_colors.colors:
            r, g, b = color.color.red, color.color.green, color.color.blue
            hsv = self._rgb_to_hsv(r, g, b)
            colors.append({
                'hsv': hsv,
                'score': color.score,
                'rgb': (r, g, b)
            })

        risk_score = self._calculate_risk_score(properties)
        return colors, risk_score

    def _calculate_confidence_score(self, quality: ImageQualityMetrics, objects) -> float:
        """解析結果の信頼度スコアを計算"""
        base_score = 1.0
        
        # 画質による減点
        if quality.is_blurry:
            base_score *= 0.5
        if not quality.has_proper_lighting:
            base_score *= 0.7
        if not quality.has_detected_nail:
            base_score *= 0.3
            
        # オブジェクト検出の信頼度を考慮
        if objects:
            avg_confidence = sum(obj.score for obj in objects) / len(objects)
            base_score *= avg_confidence
            
        return base_score

    def _calculate_risk_score(self, properties) -> float:
        """
        色解析結果から貧血リスクスコアを計算
        
        爪の色が薄いピンク/白っぽい場合にリスクが高いと判定
        健康な爪の色相は赤みがかったピンクで、彩度が中程度以上
        """
        # 主要な色の抽出と HSV 変換
        colors = []
        for color in properties.dominant_colors.colors:
            r, g, b = color.color.red, color.color.green, color.color.blue
            score = color.score
            hsv = self._rgb_to_hsv(r, g, b)
            colors.append({
                'hsv': hsv,
                'score': score,
                'rgb': (r, g, b)
            })

        # リスクスコアの計算
        risk_scores = []
        for color in colors:
            h, s, v = color['hsv']
            
            # 色相による評価（0-360度）
            # 健康な爪は0度付近（赤）から30度付近（ピンク）
            hue_score = min(abs(h - 0) / 180.0, abs(h - 360) / 180.0)
            if 0 <= h <= 30:
                hue_score = 0.3  # 健康的な色相範囲
            
            # 彩度による評価（0-100%）
            # 健康な爪は彩度が40-80%程度
            saturation_score = 0.0
            if s < 40:  # 彩度が低すぎる（白っぽい）
                saturation_score = 0.8
            elif s > 80:  # 彩度が高すぎる（不自然）
                saturation_score = 0.5
            
            # 明度による評価（0-100%）
            # 健康な爪は明度が60-90%程度
            value_score = 0.0
            if v < 60:  # 暗すぎる
                value_score = 0.7
            elif v > 90:  # 明るすぎる（白っぽい）
                value_score = 0.9
            
            # 総合スコア（重み付け）
            risk_score = (
                0.4 * hue_score +      # 色相の重要度
                0.4 * saturation_score + # 彩度の重要度
                0.2 * value_score       # 明度の重要度
            )
            
            risk_scores.append(risk_score * color['score'])
        
        # 重み付き平均でリスクスコアを算出（0-1の範囲）
        final_score = sum(risk_scores)
        return min(max(final_score, 0.0), 1.0)

    def _rgb_to_hsv(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """RGB色空間からHSV色空間への変換"""
        r, g, b = r/255.0, g/255.0, b/255.0
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        # 色相（Hue）の計算
        h = 0
        if diff == 0:
            h = 0
        elif cmax == r:
            h = 60 * ((g-b)/diff % 6)
        elif cmax == g:
            h = 60 * ((b-r)/diff + 2)
        else:
            h = 60 * ((r-g)/diff + 4)
        
        if h < 0:
            h += 360

        # 彩度（Saturation）の計算
        s = 0 if cmax == 0 else (diff / cmax) * 100

        # 明度（Value）の計算
        v = cmax * 100

        return h, s, v 