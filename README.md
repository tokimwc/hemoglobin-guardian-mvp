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

## 注意事項
- 本アプリは貧血リスクの**参考情報**を提供するものです
- 医療機器としての認証は受けていません
- 健康上の問題が疑われる場合は医師の診断を優先してください

## ライセンス
MIT License

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

## ライセンス
- [MIT License](LICENSE) (例)

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

### テストケース
1. **Gemini API統合テスト**
   - 低リスク時のアドバイス生成
   - 高リスク時のアドバイス生成
   - 警告付きのアドバイス生成
   - レスポンス形式の検証
   
2. **テストカバレッジ**
   - 目標: 80%以上
   - 現在: 81%達成
   - 未カバー: エラーハンドリング部分

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

