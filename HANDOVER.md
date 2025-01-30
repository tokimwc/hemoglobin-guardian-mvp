# 実装引継書

## プロジェクト概要
ヘモグロビンガーディアンは、スマートフォンのカメラを使用して貧血リスクを簡易チェックし、AIによるアドバイスを提供するアプリケーションです。

## 技術スタック
- フロントエンド: Flutter 3.27.2
- バックエンド: Python (Cloud Run)
- データベース: Cloud Firestore
- AI/ML: Vision AI, Vertex AI (Gemini)
- 認証: Firebase Authentication

## 実装済み機能

### 1. データモデル
#### `AnalysisRecord`クラス
- Freezedを使用した不変オブジェクトの実装
- Firestoreとの連携（`toFirestore`/`fromFirestore`メソッド）
- 以下のフィールドを保持：
  - id: 記録ID
  - userId: ユーザーID
  - createdAt: 作成日時
  - riskLevel: リスクレベル
  - riskScore: リスクスコア
  - adviceText: AIアドバイス
  - imageUrl: 画像URL（オプション）
  - mlKitResults: ML Kit解析結果（オプション）
  - visionAiResults: Vision AI解析結果（オプション）

### 2. 画面実装
#### HomeScreen
- 解析開始ボタン
- 履歴表示ボタン
- シンプルなUI構成

#### HistoryScreen
- 解析履歴の一覧表示
- 日時フォーマット（intlパッケージ使用）
- リスクレベルと画像のプレビュー表示
- ローディング状態とエラー処理

### 3. バックエンド実装
#### Gemini API連携 ✅
- アドバイス生成機能の実装完了
- リスクレベルに応じた分岐処理
- エラーハンドリングの実装
- キャッシュ機能の実装
- 非同期処理の最適化
- テストケースの整備

#### エラーハンドリング ✅
- エラーレスポンスの標準化
- バリデーションエラーの実装
- システムエラーの実装
- タイムアウト処理の実装

#### テスト実装 ✅
- 統合テストの実装
- パフォーマンステストの実装
- 並行リクエストテストの実装
- エラーケースのテスト

## 今後の実装タスク

### 優先度高
1. **Cloud Run連携**
   - [ ] APIエンドポイントの実装（/analyze, /advice）
   - [ ] フロントエンドとの連携テスト
   - [ ] デプロイ設定の最終確認

2. **Vision AI実装**
   - [ ] 画像解析機能の実装
   - [ ] リスク判定ロジックの実装
   - [ ] ML Kitとの統合検証

3. **フロントエンド連携**
   - [ ] 画像送信機能の実装
   - [ ] レスポンス表示の実装
   - [ ] エラーハンドリングUIの実装

### 優先度中
1. **Firestore連携**
   - [ ] 解析結果の保存機能
   - [ ] 履歴取得機能の実装
   - [ ] セキュリティルールの設定

2. **UI/UX改善**
   - [ ] ローディング表示の実装
   - [ ] エラー表示の改善
   - [ ] 成功時アニメーションの追加

3. **テスト整備**
   - [ ] フロントエンドの単体テスト
   - [ ] Widgetテストの実装
   - [ ] E2Eテストの実装

### 優先度低
1. **パフォーマンス最適化**
   - [ ] API呼び出しの最適化
   - [ ] 画像処理の効率化
   - [ ] キャッシュ戦略の検討

2. **セキュリティ強化**
   - [ ] 認証フローの改善
   - [ ] APIキーの管理方法見直し
   - [ ] エラーログの暗号化

## 注意点・課題
1. Firestoreのセキュリティルール実装が必要
2. 画像の一時保存方法の検討
3. APIキーの安全な管理方法の確立
4. パフォーマンス最適化（特に画像処理時）

## テスト環境
- Android Emulator: SDK Platform 34
- 実機テスト: 未実施

## デプロイ情報

### Cloud Run
- サービス名: [SERVICE_NAME]
- リージョン: asia-northeast1
- エンドポイント: 環境変数`BACKEND_URL`を参照
- 主要エンドポイント:
  - ヘルスチェック: GET /health
  - 画像解析: POST /analyze
  - 履歴取得: GET /history/{user_id}

### Artifact Registry
- リポジトリ名: [REPOSITORY_NAME]
- リージョン: asia-northeast1
- イメージパス: asia-northeast1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/backend

### 環境変数設定
必要な環境変数は各環境の`.env`ファイルに設定してください：

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

### デプロイ手順
1. Dockerイメージのビルド
```bash
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

注意：実際の値は`.env`ファイルで管理し、GitHubにはプッシュしないでください。

## 開発環境セットアップ
1. 必要なツール
   - Flutter SDK 3.27.2以上
   - Android Studio
   - Python 3.9以上
   - Firebase CLI

2. 環境変数
   - GOOGLE_APPLICATION_CREDENTIALS
   - FIREBASE_CONFIG
   - VERTEX_AI_LOCATION

## 参考資料
- [Flutter公式ドキュメント](https://flutter.dev/docs)
- [Firebase Flutter Codelab](https://firebase.google.com/codelabs/firebase-get-to-know-flutter)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs) 