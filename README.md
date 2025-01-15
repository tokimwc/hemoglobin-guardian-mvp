# ヘモグロビンガーディアン (MVP)

本リポジトリは、貧血リスクを簡易チェック＆AIアドバイスを行う**MVP版**アプリです。  
Flutter + Cloud Run + Firebase + Vision AI (AutoML/Vertex AI) 等を活用し、ハッカソン向けに構築しています。

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

---

