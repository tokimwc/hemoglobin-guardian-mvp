import os
import base64
import json
from pathlib import Path

def generate_test_data():
    """画像ファイルをBase64エンコードしてJSONファイルを生成する"""
    
    # 画像ディレクトリのパス
    image_dir = Path(__file__).parent / 'images'
    
    # Base64エンコードされたデータを格納する辞書
    test_data = {}
    
    # 画像ファイルを処理
    for image_file in image_dir.glob('*.jpg'):
        # ファイル名から識別子を生成（例：healthy_nail.jpg → healthy_nail）
        identifier = image_file.stem
        
        # 画像ファイルを読み込みBase64エンコード
        with open(image_file, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
        # 辞書に追加
        test_data[identifier] = base64_data
    
    # JSONファイルに保存
    output_file = Path(__file__).parent / 'test_images.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"テストデータを生成しました: {output_file}")

if __name__ == '__main__':
    generate_test_data() 