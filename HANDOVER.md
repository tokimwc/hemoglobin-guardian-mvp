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

### 3. ルーティング
- go_routerを使用した画面遷移の実装
- 認証状態に基づくリダイレクト処理
- 以下のルートを実装：
  - `/`: HomeScreen
  - `/camera`: CameraScreen
  - `/analysis`: AnalysisScreen
  - `/history`: HistoryScreen

### 4. 依存パッケージ
- intl: ^0.19.0（国際化対応）
- freezed: ^2.4.5（データモデル）
- cloud_firestore: ^4.17.5（Firestore連携）
- その他必要なパッケージ（pubspec.yamlを参照）

## 今後の実装タスク

### 優先度高
1. バックエンド連携
   - Cloud Run APIとの通信実装
   - エラーハンドリング

2. 画像解析機能
   - Vision AIによる画像解析
   - ML Kitとの統合

3. AIアドバイス生成
   - Gemini APIによるアドバイス生成
   - プロンプトの最適化

### 優先度中
1. UI/UX改善
   - ローディング表示の改善
   - エラーメッセージの改善
   - アニメーション追加

2. テスト実装
   - 単体テスト
   - 統合テスト
   - UIテスト

### 優先度低
1. オフライン対応
2. 多言語対応
3. テーマカスタマイズ

## 注意点・課題
1. Firestoreのセキュリティルール実装が必要
2. 画像の一時保存方法の検討
3. APIキーの安全な管理方法の確立
4. パフォーマンス最適化（特に画像処理時）

## テスト環境
- Android Emulator: SDK Platform 34
- 実機テスト: 未実施

## デプロイ手順
1. フロントエンド（Flutter）
```bash
flutter build apk --release
```

2. バックエンド（Cloud Run）
```bash
cd backend
gcloud builds submit --tag gcr.io/[project-id]/hemoglobin-backend
gcloud run deploy
```

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