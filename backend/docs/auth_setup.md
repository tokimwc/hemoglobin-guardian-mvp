# 認証情報のセットアップ手順

## 1. Firebase認証情報の設定

1. [Firebase Console](https://console.firebase.google.com/) にアクセス
2. プロジェクトの設定 > サービスアカウント に移動
3. 「新しい秘密鍵の生成」をクリック
4. ダウンロードしたJSONファイルを以下の場所に配置:
   ```
   backend/credentials/firebase-service-account.json
   ```

## 2. Google Cloud認証情報の設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択
3. IAMと管理 > サービスアカウント に移動
4. 「サービスアカウントを作成」をクリック
   - 名前: `hemoglobin-guardian-service`
   - 役割:
     - Vision AI API 呼び出し
     - Vertex AI API 呼び出し
5. キーを作成（JSONタイプ）
6. ダウンロードしたJSONファイルを以下の場所に配置:
   ```
   backend/credentials/google-cloud-service-account.json
   ```

## 3. APIの有効化

Google Cloud Consoleで以下のAPIを有効化:
- Cloud Vision API
- Vertex AI API
- Cloud Storage API
- Cloud Run API

## 4. 環境変数の確認

`.env`ファイルの以下の設定が正しいことを確認:

```
FIREBASE_CREDENTIALS_PATH=./credentials/firebase-service-account.json
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-service-account.json
```

## 5. セキュリティ注意事項

- 認証情報ファイル（`*.json`）は`.gitignore`に含め、Gitにコミットしない
- 本番環境では環境変数を使用し、ファイルをデプロイしない
- 認証情報は定期的にローテーション
- 最小権限の原則に従い、必要な権限のみ付与

## 6. 動作確認

1. 認証情報の配置後、以下のコマンドでテストを実行:
```bash
cd backend
pytest tests/services/test_vision_service.py -v
pytest tests/services/test_gemini_service.py -v
```

2. テストが成功すれば認証情報は正しく設定されています。

## トラブルシューティング

1. **Firebase認証エラー**
   - Firebaseプロジェクトの設定を確認
   - サービスアカウントの権限を確認

2. **Vision AI/Vertex AIエラー**
   - APIが有効化されているか確認
   - 請求が有効になっているか確認
   - サービスアカウントの権限を確認

3. **認証情報ファイルのパスエラー**
   - `.env`ファイルのパス設定を確認
   - ファイル名が正しいか確認 