# ヘモグロビンガーディアン (MVP)

本リポジトリは、貧血リスクを簡易チェック＆AIアドバイスを行う**MVP版**アプリです。  
Flutter + Cloud Run + Firebase + Vision AI (Vertex AI) 等を活用し、ハッカソン向けに構築しています。

## 実装済み機能

### 認証機能
- Firebase Authenticationによるメール/パスワード認証
- ログイン/新規登録画面
- エラーハンドリング（日本語メッセージ）

### カメラ/ギャラリー機能
- リアルタイムカメラプレビュー
- 写真撮影機能
- ギャラリーからの画像選択
- 画像プレビュー表示

### ML Kit解析機能
- 画像ラベリング（オブジェクト検出）
- 顔検出機能
- 色解析（基本実装）
- 信頼度スコアの計算と表示
- 解析結果の視覚的表示

## 今後の展開

### 優先実装項目
1. **Firestoreデータ保存**
   - 解析結果の永続化
   - ユーザーごとの履歴管理
   - セキュリティルールの設定

2. **Vision AI連携**
   - より高度な画像解析
   - 貧血リスク推定の精度向上

3. **Gemini APIによるアドバイス生成**
   - パーソナライズされた栄養アドバイス
   - リスクレベルに応じた対策提案

## セットアップ手順

### 必要な環境
- Flutter SDK 3.27.2以上
- Dart SDK 3.6.1以上
- Android Studio Hedgehog | 2023.1.1
- Android SDK Platform 34
- Firebase プロジェクト

### インストール手順

1. リポジトリのクローン
```bash
git clone https://github.com/your-username/hemoglobin-guardian-mvp.git
cd hemoglobin-guardian-mvp
```

2. 依存関係のインストール
```bash
cd frontend
flutter pub get
```

3. Firebaseの設定
- `google-services.json`を`frontend/android/app/`に配置
- Firebase Consoleで認証機能を有効化

4. アプリの実行
```bash
flutter run
```

## テストの実行

### バックエンドのテスト

1. **テストデータの準備**
```bash
# テストデータ用のディレクトリ構造を作成
cd backend/tests/data
mkdir images

# テスト用の画像を images ディレクトリに配置
# 以下の命名規則に従ってください：
# - healthy_nail.jpg  # 健康的な爪の画像
# - medium_risk_nail.jpg  # やや貧血の可能性がある爪の画像
# - high_risk_nail.jpg  # 貧血リスクが高い爪の画像

# テストデータ（Base64エンコード）の生成
python generate_test_data.py
```

2. **ユニットテストの実行**
```bash
cd backend
python -m pytest tests/ -v
```

3. **カバレッジレポートの生成**
```bash
python -m pytest tests/ --cov=src --cov-report=html
# レポートは htmlcov/index.html で確認できます
```

### フロントエンドのテスト

1. **ウィジェットテスト**
```bash
cd frontend
flutter test test/widget_test/
```

2. **統合テスト**
```bash
flutter test integration_test/
```

### テストデータについて

テストでは、以下の2つの形式でテストデータを管理しています：

1. **元画像ファイル** (`backend/tests/data/images/`)
   - `healthy_nail.jpg`: 健康的な爪の画像
   - `medium_risk_nail.jpg`: やや貧血の可能性がある爪の画像
   - `high_risk_nail.jpg`: 貧血リスクが高い爪の画像

2. **Base64エンコードされたデータ** (`backend/tests/data/test_images.json`)
   - APIテストで使用
   - 自動テストの再現性を確保
   - CI/CDパイプラインでの実行に最適化

テストデータの更新手順：
1. 新しいテスト画像を `images/` ディレクトリに追加
2. `generate_test_data.py` を実行してJSONファイルを更新
3. 両方のファイルをバージョン管理に含める

## 開発者向け情報

### アーキテクチャ
- Riverpod + Freezedによる状態管理
- go_routerによる画面遷移
- クリーンアーキテクチャベース

### テスト実行
```bash
flutter test
```

### ビルド
```bash
# デバッグビルド
flutter build apk --debug

# リリースビルド
flutter build apk --release
```

### API仕様（OpenAPI）

本プロジェクトではOpenAPI仕様（`docs/api/openapi.yaml`）を使用してAPIを定義しています。

#### 1. API仕様の確認方法

```bash
# Swagger UIでの表示（開発環境）
cd backend
uvicorn main:app --reload
# ブラウザで http://localhost:8000/docs にアクセス
```

#### 2. コード生成

APIクライアントコードの自動生成：
```bash
# Flutterクライアントの生成
cd frontend
dart run build_runner build

# FastAPIルーティングの生成（バックエンド）
cd backend
python generate_fastapi_routes.py
```

#### 3. 主要エンドポイント

1. **画像解析 API** (`POST /analyze`)
   - 爪の画像をアップロードし、貧血リスクを推定
   - Vision AIによる画像解析
   - Gemini APIによるアドバイス生成

2. **履歴取得 API** (`GET /history/{userId}`)
   - ユーザーごとの解析履歴を取得
   - 最新の結果や過去の推移を確認

#### 4. セキュリティ

- Firebase認証トークンによる認証
- HTTPSによる通信暗号化
- レート制限の実装

## 注意事項
- 本アプリは貧血リスクの**参考情報**を提供するものです
- 医療機器としての認証は受けていません
- 健康上の問題が疑われる場合は医師の診断を優先してください

## ライセンス
[MIT License](LICENSE) - 医療免責事項付き

本ソフトウェアは医療機器ではありません。詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## コントリビューション
Issue や Pull Requestを歓迎します。

## デモ概要
- スマホカメラ（or ギャラリー）から爪の写真をアップロード
- Cloud Run でホストしたサーバーが Vision AI で画像解析し、リスクを判定
- Vertex AI (Gemini API) で貧血予防の栄養アドバイスを生成
- Firebase でユーザー情報や解析履歴を管理

## ディレクトリ構成

```
hemoglobin-guardian-mvp/
├── README.md
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── src/
├── frontend/
│   ├── pubspec.yaml
│   └── lib/
│       ├── main.dart
│       └── src/
│           ├── components/
│           │   ├── camera/     # カメラ・画像選択UI
│           │   └── analysis/   # 解析結果表示UI
│           ├── models/         # データモデル
│           ├── providers/      # 状態管理
│           └── services/       # APIクライアント
├── firebase/
│   ├── firebase.json
│   └── firestore.rules
└── docs/
    ├── architecture-diagram.png
    └── requirements.md
```

## 開発環境のセットアップ

### 重要な注意点（Windows環境）

1. **作業ディレクトリ**
   - プロジェクトルート: `C:\dev\hemoglobin-guardian-mvp`
   - バックエンド: `C:\dev\hemoglobin-guardian-mvp\backend`
   - フロントエンド: `C:\dev\hemoglobin-guardian-mvp\frontend`

2. **パスの指定**
   - Windowsでは`\`（バックスラッシュ）を使用
   - 例: `tests\integration\test_gemini_integration.py`
   - 相対パスよりも絶対パスの使用を推奨（特にテスト実行時）

3. **仮想環境の活性化**
   ```batch
   # プロジェクトルートから
   cd C:\dev\hemoglobin-guardian-mvp\backend
   .\venv\Scripts\activate
   ```

4. **テスト実行**
   ```batch
   # 統合テスト
   python -m pytest tests\integration\test_gemini_integration.py -v

   # パフォーマンステスト
   python -m pytest tests\performance\test_gemini_performance.py -v

   # カバレッジレポート
   python -m pytest --cov=src tests\ --cov-report=term-missing
   ```

5. **トラブルシューティング**
   - パスが見つからないエラー → 絶対パスを使用
   - モジュールが見つからないエラー → 仮想環境が有効化されているか確認
   - 権限エラー → 管理者権限で実行

### 1. Firebase プロジェクト作成
1. [Firebaseコンソール](https://console.firebase.google.com/) で新規プロジェクトを作成
2. Authentication や Firestore の有効化
3. `firebase/` ディレクトリ内の設定ファイル（`firebase.json`など）を更新  
   - プロジェクトIDや認証方式を記載
4. **重要:** 秘密鍵やサービスアカウントJSONは `.gitignore` で管理し、GitHubにはアップロードしない

### 2. Google Cloud プロジェクト作成
1. [Google Cloud コンソール](https://console.cloud.google.com/) で新規プロジェクトを作成
2. Vision AI, Vertex AI, Cloud Run, Container Registry などのAPIを有効化
3. サービスアカウントを作成し、ローカルやCloud Runで使用する認証情報を取得  
   - こちらも**GitHubに含めない**ように注意

### 3. ローカル環境での開発 (バックエンド)
1. **Python** のバージョン(例: 3.9)をインストール
2. backend ディレクトリへ移動し、必要に応じて仮想環境を作成
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   ```
3. 依存ライブラリをインストール
   ```bash
   pip install -r requirements.txt
   ```
4. ローカル実行
   ```bash
   python main.py
   ```
   - ポート番号等を指定してAPIを起動し、`http://localhost:8000` などにアクセスしてテスト

### 4. ローカル環境での開発 (フロントエンド)
1. [Flutter SDK](https://docs.flutter.dev/get-started/install) をインストール
2. frontend ディレクトリへ移動
   ```bash
   cd frontend
   flutter pub get
   ```
3. Freezedのコード生成
   ```bash
   dart run build_runner build
   ```
4. アプリケーションの実行
   ```bash
   # Windowsの場合
   flutter run -d windows
   
   # Android/iOSの場合
   flutter run
   ```

#### フロントエンド実装状況
- [x] カメラ/ギャラリーからの画像選択
- [x] 画像プレビュー表示
- [x] 解析画面への遷移
- [x] APIクライアントの基本実装
- [x] 解析結果表示UI
- [ ] ユーザー認証
- [ ] 履歴表示
- [ ] 設定画面

### 5. デプロイ (Cloud Run)
1. Dockerfile を用いてコンテナイメージをビルド & Container Registryへプッシュ
   ```bash
   cd backend
   gcloud builds submit --tag gcr.io/[your-gcp-project]/hemoglobin-backend
   ```
2. Cloud Runにデプロイ
   ```bash
   gcloud run deploy hemoglobin-backend \
     --image gcr.io/[your-gcp-project]/hemoglobin-backend \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated
   ```
3. デプロイ完了後、APIエンドポイントのURLをフロントエンドで使用

### 6. Firebase ホスティング (必要に応じて)
- Flutter Webとしてビルドし、`build/web` をFirebase Hostingへアップロードする場合など

## 注意・免責事項
- 本アプリは貧血リスクの**参考情報**を提供するものであり、医療機器としての精度や認証はありません。  
- 万一、健康上の問題が疑われる場合は医師の診断を優先してください。

## 貢献方法
- Issue や Pull Requestを歓迎します。詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

## テスト実行

### 1. 統合テスト
```bash
# バックエンドディレクトリに移動
cd backend

# 仮想環境のアクティブ化
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Gemini API統合テストの実行
python -m pytest tests/integration/test_gemini_integration.py -v

# カバレッジレポートの生成
python -m pytest --cov=src tests/ --cov-report=term-missing
```

## 開発者向け注意事項

### Gemini API利用時の注意点
1. エラーハンドリング
   - タイムアウトは4秒に設定されています
   - エラー時は適切なフォールバックレスポンスを返すようにしてください
   - 入力値のバリデーションを必ず実装してください

2. パフォーマンス要件
   - 通常の応答時間：10秒以内
   - エラー時の応答時間：5秒以内
   - メモリ使用量：通常50MB以内、エラー時10MB以内
   - 同時リクエスト数：最大2件

3. APIクォータ制限
   - 同時リクエスト時は10秒の間隔を空けてください
   - エラー発生時はリトライ間隔を適切に設定してください
   - テスト実行時は特にクォータ制限に注意してください

4. テスト実行時の注意
   - 仮想環境が有効化されていることを確認
   - 正しいPythonバージョンを使用（3.9以上）
   - Windowsの場合、パスの区切り文字に注意（バックスラッシュを使用）

### 開発環境セットアップ
（既存の内容は維持）

---

## プロジェクト概要
ヘモグロビンガーディアンは、スマートフォンのカメラを使用して貧血リスクを簡易チェックし、AIによるアドバイスを提供するアプリケーションです。

## 技術スタック
- フロントエンド: Flutter 3.27.2
- バックエンド: Python 3.9+ (Cloud Run)
- データベース: Cloud Firestore
- AI/ML: Vision AI, Vertex AI (Gemini)
- 認証: Firebase Authentication
- コンテナ: Docker

## セットアップ手順

### 1. 必要なツール
- Flutter SDK 3.27.2以上
- Python 3.9以上
- Docker
- Google Cloud CLI
- Firebase CLI

### 2. 環境変数の設定
プロジェクトルートに`.env`ファイルを作成し、必要な環境変数を設定してください。

#### バックエンド (backend/.env)
```env
# Firebase設定
FIREBASE_CREDENTIALS_PATH=./credentials/firebase-service-account.json

# Google Cloud設定
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-service-account.json
GOOGLE_CLOUD_PROJECT=[PROJECT_ID]
GOOGLE_CLOUD_LOCATION=asia-northeast1

# Vision AI設定
VISION_AI_LOCATION=asia-northeast1

# Vertex AI (Gemini)設定
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL_ID=gemini-1.5-pro

# アプリケーション設定
BACKEND_URL=[CLOUD_RUN_URL]
```

#### フロントエンド (frontend/.env)
```env
BACKEND_URL=[CLOUD_RUN_URL]
```

### 3. バックエンドのセットアップ
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windowsの場合: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 4. フロントエンドのセットアップ
```bash
cd frontend
flutter pub get
```

## 開発環境での実行

### バックエンド
```bash
cd backend
.\venv\Scripts\activate  # Windowsの場合
source venv/bin/activate # macOS/Linuxの場合
python main.py
```

### フロントエンド
```bash
cd frontend
flutter run
```

## デプロイ

### バックエンドのデプロイ
1. Dockerイメージのビルド
```bash
cd backend
docker build -t [SERVICE_NAME] .
```

2. Artifact Registryへのプッシュ
```bash
docker tag [SERVICE_NAME] asia-northeast1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/backend:v1
docker push asia-northeast1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/backend:v1
```

3. Cloud Runへのデプロイ
```bash
gcloud run deploy [SERVICE_NAME] \
  --image asia-northeast1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/backend:v1 \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## APIエンドポイント
- ヘルスチェック: GET /health
- 画像解析: POST /analyze
- 履歴取得: GET /history/{user_id}

## 注意事項
- 環境変数やAPIキーなどの機密情報は必ず`.env`ファイルで管理し、Gitにコミットしないでください
- 本番環境へのデプロイ前に、セキュリティ設定を必ず確認してください
- 大きな画像ファイルを扱う際は、メモリ使用量に注意してください

## Docker開発環境

### Dockerビルドスクリプト
バックエンドのビルドとデプロイを自動化する`deploy.bat`スクリプトを提供しています。

#### 使用方法
```batch
# バックエンドディレクトリに移動
cd backend

# スクリプトを実行
deploy.bat
```

#### スクリプトの機能
- Dockerイメージのビルド
- エラー時の自動リトライ（最大3回）
- システムリソースの自動クリーンアップ
- 詳細なログ出力

#### 設定可能なパラメータ
- `DOCKER_MEMORY`: メモリ制限（デフォルト: 4GB）
- `DOCKER_MEMORY_SWAP`: スワップメモリ制限（デフォルト: 4GB）
- `MAX_RETRIES`: 最大リトライ回数（デフォルト: 3）
- `RETRY_DELAY`: リトライ間隔（秒、デフォルト: 30）

#### エラーハンドリング
1. ビルド失敗時
   - 自動的にクリーンアップを実行
   - メモリ制限を調整して再試行
   - エラーログを`build_error.log`に保存

2. トラブルシューティング
   - エラーログを確認: `build_error.log`
   - Dockerシステムの状態確認: `docker system df`
   - キャッシュのクリア: `docker system prune -af`

### 開発時の注意事項
1. メモリ使用量
   - 初回ビルド時: 4GB
   - リトライ時: 3GB
   - 必要に応じて`deploy.bat`内の設定を調整

2. ログ管理
   - ビルドログ: `build_error.log`
   - 詳細なデバッグ情報を含む

3. 環境変数
   - `.env`ファイルで管理
   - 機密情報は`.gitignore`に追加

