from google.cloud import vision
from typing import List, Tuple, Dict
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

class VisionService:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
        self._executor = ThreadPoolExecutor()

    async def analyze_image(self, image_content: bytes) -> float:
        """
        画像を非同期で解析し、貧血リスクスコアを算出
        
        Args:
            image_content: 画像のバイトデータ
            
        Returns:
            float: 0.0 ~ 1.0のリスクスコア（高いほどリスクが高い）
        """
        image = vision.Image(content=image_content)
        
        def _analyze():
            return self.client.image_properties(image=image)
        
        # Vision APIの呼び出しを非同期化
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(self._executor, _analyze)
        
        return self._calculate_risk_score(response.image_properties_annotation)

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