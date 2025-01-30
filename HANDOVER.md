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
#### Vision AI実装 ✅
- 画像解析機能の実装完了
- リスク判定ロジックの実装完了
- 色解析（HSV色空間）の実装
- 爪検出機能の実装
- 画質チェック機能の実装
- エラーハンドリングの実装

#### APIエンドポイント実装 ✅
- `/analyze`エンドポイントの実装
- `/health`エンドポイントの実装
- `/history/{user_id}`エンドポイントの実装
- CORSミドルウェアの設定
- エラーハンドリングの実装

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
   - [x] APIエンドポイントの実装
   - [ ] フロントエンドとの連携テスト
   - [ ] デプロイ設定の最終確認
   - [ ] 本番環境用CORSの設定
   - [ ] 環境変数の設定確認

2. **フロントエンド連携**
   - [ ] 画像送信機能の実装
   - [ ] レスポンス表示の実装
   - [ ] エラーハンドリングUIの実装
   - [ ] ローディング表示の実装
   - [ ] 解析結果の視覚的表示

3. **Firestore連携**
   - [ ] 解析結果の保存機能
   - [ ] 履歴取得機能の実装
   - [ ] セキュリティルールの設定

### 優先度中
1. **UI/UX改善**
   - [ ] ローディング表示の実装
   - [ ] エラー表示の改善
   - [ ] 成功時アニメーションの追加

2. **テスト整備**
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

# 引き継ぎ書

## 2024年1月30日の作業内容

### 1. Dockerビルドプロセスの改善
#### 実施内容
- `deploy.bat`スクリプトの改善
  - エラーハンドリングの強化
  - 自動リトライメカニズムの実装
  - メモリ管理の最適化
  - ログ出力の改善

#### 具体的な改善点
1. エラーハンドリング
   - ビルド失敗時の自動リトライ（最大3回）
   - エラーログの詳細な記録
   - クリーンアップ処理の自動化

2. メモリ管理
   - 初期メモリ制限: 4GB
   - リトライ時の自動調整: 3GB
   - スワップメモリの最適化

3. ログ管理
   - `build_error.log`の導入
   - デバッグ情報の充実
   - エラーメッセージの日本語化

### 2. ドキュメント整備
- README.mdの更新
  - Dockerビルド手順の追加
  - トラブルシューティングガイドの作成
  - 環境変数の説明追加

### 3. 今後の課題
1. CI/CD
   - GitHub Actionsとの連携
   - 自動テストの追加
   - デプロイ自動化の完成

2. パフォーマンス
   - ビルド時間の短縮
   - キャッシュ戦略の最適化
   - マルチステージビルドの検討

3. セキュリティ
   - 環境変数の暗号化
   - イメージスキャンの導入
   - アクセス制御の強化

### 4. 注意点
1. デプロイ時
   - 必ず`.env`ファイルの存在を確認
   - メモリ使用量に注意
   - ログファイルの定期的なクリーンアップ

2. トラブルシューティング
   - `build_error.log`を確認
   - `docker system df`でリソース確認
   - 必要に応じて`docker system prune -af`を実行

### 5. 連絡先
- 技術的な質問: [担当者名]
- 運用に関する質問: [運用担当者名]
- 緊急時の連絡先: [緊急連絡先]

## 次回以降の作業予定
1. Cloud Run デプロイスクリプトの実装
2. CI/CD パイプラインの構築
3. モニタリング基盤の整備

## 注意事項
- ビルド時のメモリ使用量に注意
- エラーログは`build_error.log`を確認
- 環境変数は`.env`ファイルで管理 