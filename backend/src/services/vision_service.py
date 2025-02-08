from google.cloud import vision
from typing import List, Tuple, Dict, Optional, Any
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from dataclasses import dataclass
import os
import logging

logger = logging.getLogger(__name__)

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
        self._executor = ThreadPoolExecutor(max_workers=3)
    
    async def analyze_image(self, image_content: bytes) -> Dict[str, Any]:
        """画像を解析し、貧血リスクを評価します"""
        try:
            # 非同期でVision APIを呼び出すためにループを取得
            loop = asyncio.get_event_loop()
            
            # Vision APIリクエストの準備
            image = vision.Image(content=image_content)
            
            # 複数の解析を並行して実行
            tasks = [
                loop.run_in_executor(None, self.client.face_detection, image),
                loop.run_in_executor(None, self.client.image_properties, image),
                loop.run_in_executor(None, self.client.object_localization, image)
            ]
            
            # 全ての解析結果を待機
            face_response, properties_response, object_response = await asyncio.gather(*tasks)
            
            # 顔の検出結果を処理
            faces = face_response.face_annotations
            face_confidence = faces[0].detection_confidence if faces else 0.0
            
            # 色解析
            colors = []
            if properties_response.image_properties_annotation.dominant_colors:
                for color in properties_response.image_properties_annotation.dominant_colors.colors:
                    colors.append({
                        'red': color.color.red,
                        'green': color.color.green,
                        'blue': color.color.blue,
                        'score': color.score
                    })
            
            # 画質評価
            quality_metrics = self._check_image_quality(properties_response.image_properties_annotation)
            
            # 爪の検出確認
            has_nail = self._detect_nail_region(object_response.localized_object_annotations)
            quality_metrics.has_detected_nail = has_nail
            
            # リスクスコアの計算
            risk_score = self._calculate_risk_score(properties_response.image_properties_annotation)
            
            return {
                "risk_score": risk_score,
                "confidence_score": max(face_confidence, 0.5),  # 最低0.5の信頼度を保証
                "detected_colors": colors,
                "is_blurry": quality_metrics.is_blurry,
                "brightness_score": quality_metrics.brightness_score,
                "has_proper_lighting": quality_metrics.has_proper_lighting,
                "has_detected_nail": quality_metrics.has_detected_nail
            }
            
        except Exception as e:
            logger.error(f"Vision API解析中にエラーが発生: {str(e)}", exc_info=True)
            raise Exception(f"画像解析に失敗しました: {str(e)}")

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
        """画像の品質を評価します"""
        # 明るさの評価
        brightness_score = 0.0
        has_proper_lighting = False
        
        if properties.dominant_colors:
            # RGBの平均値から明るさを計算
            total_brightness = 0
            total_weight = 0
            
            for color in properties.dominant_colors.colors:
                rgb_avg = (color.color.red + color.color.green + color.color.blue) / 3
                total_brightness += rgb_avg * color.score
                total_weight += color.score
            
            if total_weight > 0:
                brightness_score = total_brightness / total_weight / 255
                has_proper_lighting = 0.3 <= brightness_score <= 0.7
        
        # ぼかしの検出（サンプル実装）
        is_blurry = brightness_score < 0.2
        
        return ImageQualityMetrics(
            is_blurry=is_blurry,
            brightness_score=brightness_score,
            has_proper_lighting=has_proper_lighting,
            has_detected_nail=False  # 初期値、後で更新
        )

    def _detect_nail_region(self, objects) -> bool:
        """爪領域の検出を試みます（改善版）"""
        # 拡張した爪関連のラベル
        nail_related_labels = {
            'finger', 'hand', 'nail', 'skin', 'thumb', 'fingernail',
            'body_part', 'joint', 'flesh', 'digit', 'manicure',
            'cuticle', 'gesture', 'finger_joint', 'palm', 'wrist',
            'knuckle', 'human_body', 'tissue', 'limb', 'close up',
            'macro photography', 'detail', 'texture', 'surface',
            'skin tone', 'body', 'photograph', 'finger tip',
            'extremity', 'person', 'human', 'anatomy',
            'part', 'organ', 'muscle', 'bone',
            # 新たなキーワードを追加
            'nail bed', 'nail plate', 'finger nail', 'nail art', 'artificial nails',
            'cosmetics', 'beauty', ' 指の爪', '爪のケア', 'ネイル' # 日本語ラベルも追加
        }

        # 信頼度の閾値をさらに緩和
        high_confidence_threshold = 0.08  # さらに低い閾値
        medium_confidence_threshold = 0.01  # さらに低い閾値

        # 方法1: 高信頼度の検出（部分一致を含む）
        for obj in objects:
            obj_name = obj.name.lower().replace('_', ' ')
            if obj.score >= high_confidence_threshold:
                if obj_name in nail_related_labels:
                    return True
                # 部分一致チェック
                if any(label in obj_name or obj_name in label or
                       any(word in obj_name.split() for word in label.split())
                       for label in nail_related_labels):
                    return True

        # 方法2: 中程度の信頼度の検出
        medium_confidence_objects = []
        for obj in objects:
            obj_name = obj.name.lower().replace('_', ' ')
            if medium_confidence_threshold <= obj.score < high_confidence_threshold:
                if obj_name in nail_related_labels:
                    medium_confidence_objects.append(obj)
                elif any(label in obj_name or obj_name in label or
                         any(word in obj_name.split() for word in label.split())
                         for label in nail_related_labels):
                    medium_confidence_objects.append(obj)
                if len(medium_confidence_objects) >= 2:
                    return True

        # 方法3: バウンディングボックス分析（細かいオブジェクトに対応）
        for obj in objects:
            box = obj.bounding_poly.normalized_vertices
            center_x = (box[0].x + box[2].x) / 2
            center_y = (box[0].y + box[2].y) / 2
            width = abs(box[2].x - box[0].x)
            height = abs(box[2].y - box[0].y)
            area = width * height
            aspect_ratio = width / height if height > 0 else 0

            # 小さなオブジェクトも検出するため、面積の閾値を下げ、アスペクト比の範囲を拡大
            if (0.0 <= center_x <= 1.0 and
                0.0 <= center_y <= 1.0 and
                0.0005 <= area <= 0.5 and # 面積の閾値をさらに下げる
                0.01 <= aspect_ratio <= 30.0): # アスペクト比の範囲をさらに拡大
                return True

        # 方法4: さらなる改善策として、Vertex AI SDK を利用した高度なオブジェクト検出に切り替えることも検討できます。

        return False

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
        if objects and len(objects) > 0:
            avg_confidence = sum(obj.score for obj in objects) / len(objects)
            base_score *= avg_confidence
            
        return base_score

    def _calculate_risk_score(self, properties) -> float:
        """色情報から貧血リスクスコアを計算します"""
        if not properties.dominant_colors:
            return 0.5  # デフォルト値
        
        # 爪の健康的な色の範囲（RGB）
        healthy_nail_color = {
            'red': (220, 255),
            'blue': (180, 220),
            'green': (180, 220)
        }
        
        risk_score = 0.5
        total_weight = 0
        
        for color in properties.dominant_colors.colors:
            # 各色チャンネルの評価
            r_score = self._evaluate_color_channel(color.color.red, healthy_nail_color['red'])
            g_score = self._evaluate_color_channel(color.color.green, healthy_nail_color['green'])
            b_score = self._evaluate_color_channel(color.color.blue, healthy_nail_color['blue'])
            
            # 色の評価スコアを重み付けして合算
            color_score = (r_score + g_score + b_score) / 3
            risk_score += color_score * color.score
            total_weight += color.score
        
        if total_weight > 0:
            risk_score = risk_score / total_weight
        
        # スコアを0-1の範囲に正規化
        return max(0.0, min(1.0, risk_score))

    def _evaluate_color_channel(self, value: int, range_tuple: tuple) -> float:
        """色チャンネルの値を評価します"""
        min_val, max_val = range_tuple
        if min_val <= value <= max_val:
            return 0.3  # 健康的な範囲内
        elif value < min_val:
            return 0.7  # 貧血の可能性
        else:
            return 0.5  # 中間的な値

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
            h = 60 * ((g - b) / diff % 6)
        elif cmax == g:
            h = 60 * ((b - r) / diff + 2)
        elif cmax == b:
            h = 60 * ((r - g) / diff + 4)
        h = (h + 360) % 360

        # 彩度（Saturation）の計算
        s = 0 if cmax == 0 else (diff / cmax) * 100

        # 明度（Value）の計算
        v = cmax * 100

        return h, s, v 