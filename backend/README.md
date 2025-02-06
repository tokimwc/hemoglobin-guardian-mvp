# HemoglobinGuardian Backend

## 概要
HemoglobinGuardianは、爪の色解析を通じて貧血リスクを推定し、AIを活用した栄養アドバイスを提供するアプリケーションのバックエンドサービスです。

## 主な機能
- 爪の画像解析（Vision AI）
- 貧血リスク推定（HSV色空間解析）
- パーソナライズされた栄養アドバイス生成（Gemini）
- 解析履歴の管理（Firebase）

## 技術スタック
- Python 3.9+
- FastAPI
- Google Cloud Vision AI
- Vertex AI (Gemini)
- Firebase
- Cloud Run

## 必要要件
- Python 3.9以上
- pip（Pythonパッケージマネージャー）
- Google Cloudアカウントと認証情報
- Firebaseプロジェクト

## セットアップ手順

### 1. リポジトリのクローン
```bash
git clone [repository-url]
cd hemoglobin-guardian-mvp/backend
```

### 2. 仮想環境の作成と有効化
```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
.\\venv\\Scripts\\activate
# Unix/macOS
source venv/bin/activate
```

### 3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定
`.env`ファイルを作成し、以下の環境変数を設定：
```
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-cloud-credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id
VISION_AI_LOCATION=asia-northeast1
VERTEX_AI_LOCATION=asia-northeast1
GEMINI_MODEL_ID=gemini-1.5-pro
```

## 開発サーバーの起動
```bash
python main.py
```
サーバーは`http://localhost:8080`で起動します。

## APIエンドポイント

### 画像解析 API
- エンドポイント: `/analyze`
- メソッド: POST
- Content-Type: multipart/form-data
- パラメータ:
  - file: 画像ファイル（JPG/PNG）

```bash
curl -X POST -F "file=@test_image.jpg" http://localhost:8080/analyze
```

### ヘルスチェック
- エンドポイント: `/health`
- メソッド: GET

```bash
curl http://localhost:8080/health
```

### 解析履歴取得
- エンドポイント: `/history/{user_id}`
- メソッド: GET
- パラメータ:
  - user_id: ユーザーID

```bash
curl http://localhost:8080/history/user123
```

## テスト実行

### 統合テスト
```bash
python -m pytest tests/integration/test_gemini_integration.py -v
```

### パフォーマンステスト
```bash
python -m pytest tests/performance/test_gemini_performance.py -v
```

### カバレッジレポート生成
```bash
python -m pytest --cov=src tests/ --cov-report=term-missing
```

## デプロイ
Cloud Runへのデプロイは、CI/CDパイプラインを通じて自動化されています。

### 手動デプロイ（必要な場合）
```bash
gcloud run deploy hemoglobin-backend \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated
```

## トラブルシューティング

### よくある問題と解決方法
1. ポート8080が使用中の場合
```bash
# Windowsの場合
netstat -ano | findstr :8080
taskkill /F /PID <PID>
```

2. 環境変数が認識されない場合
- `.env`ファイルの存在を確認
- 仮想環境が有効化されているか確認

3. 依存関係のエラー
```bash
pip install --upgrade -r requirements.txt
```

## ライセンス
このプロジェクトはMITライセンスの下で公開されています。

## コントリビューション
1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 関連ドキュメント
- [アーキテクチャ設計書](./docs/ARCHITECTURE.md)
- [API仕様書](./docs/API.md)
- [引き継ぎ書](./docs/HANDOVER.md) 