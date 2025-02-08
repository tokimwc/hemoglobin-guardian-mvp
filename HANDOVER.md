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
#### `AnalysisResult`クラス ✅
- Freezedを使用した不変オブジェクトの実装
- 以下のフィールドを保持：
  - riskLevel: リスクレベル
  - riskScore: リスクスコア
  - adviceText: AIアドバイス
  - qualityMetrics: 画質メトリクス
  - warnings: 警告メッセージ
  - createdAt: 作成日時
  - imageUrl: 画像URL（オプション）
  - visionAiResults: Vision AI解析結果（オプション）
  - mlKitResults: ML Kit解析結果（オプション）

#### `AnalysisHistory`クラス ✅
- Freezedを使用した不変オブジェクトの実装
- 以下のフィールドを保持：
  - id: 履歴ID
  - userId: ユーザーID
  - result: 解析結果
  - createdAt: 作成日時
  - note: メモ（オプション）

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

#### AnalysisScreen ✅
- 画像解析UI
- ローディング表示
- エラー表示
- 結果表示カード
- 画質警告表示
- 保存機能（Firestoreとの連携は未実装）

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
  - CORSとセキュリティテスト
  - プリフライトリクエストの検証
  - セキュリティヘッダーの確認
- パフォーマンステストの実装
  - 同時リクエストの処理
  - 画像解析の応答時間
  - メモリ使用量の監視
- エラーケースのテスト
  - バリデーションエラー
  - タイムアウト処理
  - 不正なリクエスト

### 4. サービス実装
#### ApiService ✅
- 画像解析エンドポイント連携
- ヘルスチェック機能
- 履歴取得機能
- エラーハンドリング

#### FirestoreService 🚧
- [ ] 解析結果の保存機能
- [ ] 履歴取得機能
- [ ] ユーザーデータ管理
- [ ] セキュリティルール

### 5. 状態管理
#### AnalysisStateNotifier 🚧
- [x] 画像解析状態管理
- [x] エラーハンドリング
- [ ] Firestore連携
- [ ] 履歴管理

## 今後の実装タスク

### 優先度高
1. **Firestore連携**
   - [ ] `FirestoreService`クラスの実装
   - [ ] `AnalysisRecordRepository`クラスの実装
   - [ ] セキュリティルールの設定
   - [ ] インデックスの設定
   - [ ] キャッシュ戦略の実装

2. **認証機能**
   - [ ] `AuthProvider`の実装
   - [ ] ログイン/ログアウトフロー
   - [ ] ユーザープロフィール管理

3. **エラーハンドリング**
   - [ ] Firestoreエラーの処理
   - [ ] オフライン対応
   - [ ] 再試行メカニズム

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

3. Android実機デバッグの設定
   - USBデバッグを有効化
   - adb reverseを使用したポートフォワーディング
   ```bash
   # 接続されているデバイスの確認
   adb devices
   
   # 特定のデバイスに対してポートフォワーディングを設定
   adb -s [DEVICE_ID] reverse tcp:8080 tcp:8080
   ```
   - フロントエンドの`.env`ファイルで`BACKEND_URL=http://localhost:8080`を設定

注意：実際の値は`.env`ファイルで管理し、GitHubにはプッシュしないでください。

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

## 2024年2月6日の作業内容

### 1. 統合テストの完了
#### 実施内容
- フロントエンドとの統合テスト実装
  - CORSの動作確認完了
  - レート制限の検証完了
  - エラーハンドリングのテスト完了

#### テスト結果
- すべてのテストが成功
- 応答時間が目標値内
- メモリ使用量が適正範囲内

### 2. 次のステップ
1. デプロイ準備
   - Cloud Run環境変数の最終確認
   - デプロイスクリプトの検証
   - 本番環境でのテスト計画

2. フロントエンド連携
   - 実装済みAPIとの結合テスト
   - エラーハンドリングUIの実装
   - ローディング表示の実装

3. モニタリング設定
   - Cloud Loggingの設定
   - エラー通知の設定
   - パフォーマンスメトリクスの設定

### 3. 注意点
- テスト環境のレート制限は無効化されているため、本番環境では適切な設定が必要
- 非同期テストの警告（asyncio_default_fixture_loop_scope）への対応が必要
- エラーログの定期的な確認と分析が重要

## 2024年2月6日 追加作業計画

### ハッカソン提出スケジュール（2月10日締切）

#### 1. フロントエンド実装 (2/6-2/7)
##### 優先実装項目
1. 画像送信機能
   - カメラ/ギャラリーからの画像取得
   - `/analyze`エンドポイントへの送信
   - レスポンス表示UI

2. UI/UX改善
   - ローディングインジケータ
   - エラーハンドリングUI
   - 解析結果の視覚的表示

3. Firestore連携（時間があれば）
   - 解析結果の保存
   - 履歴画面の実装

#### 2. デモ準備 (2/8)
1. デモ動画シナリオ
   ```
   1. アプリ起動＆ログイン
   2. ホーム画面説明
   3. 写真撮影/選択
   4. 解析処理＆ローディング
   5. 結果表示＆AIアドバイス
   6. （オプション）履歴画面
   ```

2. UI文言サンプル
   - ホーム: "爪の色から貧血リスクをチェック"
   - 撮影前: "爪を鮮明に撮影してください"
   - 解析中: "AIが画像を分析しています..."
   - 結果表示: "分析結果とアドバイス"

#### 3. Zenn記事作成 (2/8-2/9)
1. 記事構成
   - 背景・課題
   - ソリューション概要
   - システム構成図
   - 実装の工夫
   - デモ動画
   - 今後の展望

2. 重点ポイント
   - Vision AI + Gemini APIの活用
   - Flutter×Cloud Runの連携
   - エラーハンドリング設計

#### 4. 最終調整 (2/9-2/10)
1. バグ修正
2. パフォーマンス確認
3. デモ動画の編集
4. 記事の推敲
5. 提出資料の最終確認

### 注意点
1. MVPフォーカス
   - 核となる機能（撮影→解析→表示）を優先
   - UIの完成度より機能の安定性を重視

2. デモ準備
   - 画面遷移はスムーズに
   - エラーケースも想定
   - 適切な解説コメント

3. 記事作成
   - 技術スタックの選定理由
   - 実装時の工夫点
   - 改善余地の明確化

### 開発環境
- Flutter: 3.27.2
- Python: 3.9以上
- Firebase: 最新
- エミュレータ: SDK Platform 34

### リソース
1. デザインアセット
   - ローディングアニメーション
   - 結果表示用アイコン
   - エラー表示用イラスト

2. テストデータ
   - サンプル画像セット
   - 想定される解析結果
   - エラーパターン

## セキュリティ設定
1. **Firestoreセキュリティルール**
```rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // ユーザー認証が必要
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      // 解析履歴
      match /history/{historyId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
  }
}
```

2. **インデックス設定**
```yaml
indexes:
- collection: users
  fields:
  - name: userId
    direction: ASCENDING
  - name: createdAt
    direction: DESCENDING
```

## 注意点
1. Firestoreのセキュリティルール実装が必要
2. オフライン対応の実装が必要
3. バッチ処理の検討（大量データ処理時）
4. キャッシュ戦略の最適化

## 2024年2月7日の作業内容

### 1. 画像解析機能の実装
#### 実施内容
- `AnalysisService`の実装
  - ML Kitによる画像解析機能の実装
  - 画像ラベルとテキスト認識の実装
  - エラーハンドリングの実装
  - モックデータの実装（バックエンド連携までの暫定対応）

#### 具体的な改善点
1. ML Kit実装
   - `ImageLabeler`と`TextRecognizer`の初期化
   - 画像解析メソッドの実装
   - 型変換エラーの修正

2. モックデータ
   - 一時的なFirestore処理の無効化
   - モックの解析結果の実装
   - デバッグログの追加

3. エラーハンドリング
   - `ApiException`の実装
   - 画像ファイル存在チェック
   - ML Kit解析エラーの処理

### 2. 次のステップ
1. バックエンドAPI連携
   - Vision AIによる画像解析の実装
   - Gemini APIによるアドバイス生成の実装
   - エラーハンドリングの実装

2. Firestore連携
   - 解析結果の永続化
   - 履歴機能の実装
   - セキュリティルールの設定

3. UI/UX改善
   - ローディング表示の改善
   - エラー表示の改善
   - 結果表示の視覚的強化

### 3. 注意点
1. ML Kit関連
   - `ImageLabeler`と`TextRecognizer`のリソース解放
   - メモリ使用量の監視
   - 画像サイズの最適化

2. Firestore関連
   - セキュリティルールの実装が必要
   - オフライン対応の実装が必要
   - データ構造の最適化

3. エラーハンドリング
   - 適切なエラーメッセージの表示
   - リトライメカニズムの実装
   - エラーログの収集
