from google.cloud import vision
from typing import List, Tuple
import numpy as np

class VisionService:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def analyze_image(self, image_content: bytes) -> float:
        """
        画像を解析し、貧血リスクスコアを算出
        
        Args:
            image_content: 画像のバイトデータ
            
        Returns:
            float: 0.0 ~ 1.0のリスクスコア（高いほどリスクが高い）
        """
        image = vision.Image(content=image_content)
        response = self.client.image_properties(image=image)
        return self._calculate_risk_score(response.image_properties_annotation)

    def _calculate_risk_score(self, properties) -> float:
        """
        色解析結果から貧血リスクスコアを計算
        
        爪の色が薄いピンク/白っぽい場合にリスクが高いと判定
        """
        # 主要な色の抽出
        colors = [(color.color.red, color.color.green, color.color.blue, color.score)
                 for color in properties.dominant_colors.colors]
        
        # 健康な爪の色の基準値（濃いピンク）
        healthy_nail_color = np.array([255, 192, 203])  # ピンク色のRGB
        
        # 各色の健康な爪色からの距離を計算
        risk_scores = []
        for r, g, b, score in colors:
            color = np.array([r, g, b])
            distance = np.linalg.norm(color - healthy_nail_color)
            # 距離を0-1の範囲に正規化（距離が大きいほどリスクが高い）
            normalized_distance = min(distance / 442.0, 1.0)  # 442は最大可能距離
            risk_scores.append(normalized_distance * score)
        
        # 重み付き平均でリスクスコアを算出
        return sum(risk_scores) 