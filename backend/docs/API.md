# API仕様書

## 概要
HemoglobinGuardian APIは、爪の画像解析と栄養アドバイス生成を提供するRESTful APIです。

## ベースURL
```
開発環境: http://localhost:8080
本番環境: https://hemoglobin-backend-226832076887.asia-northeast1.run.app
```

## 共通仕様

### リクエストヘッダー
```
Content-Type: application/json or multipart/form-data
Authorization: Bearer {token}  # 将来的な実装のために予約
```

### エラーレスポンス
```json
{
    "detail": {
        "message": "エラーメッセージ",
        "code": "ERROR_CODE",
        "timestamp": "2024-03-20T12:34:56.789Z"
    }
}
```

### エラーコード
| コード | 説明 |
|--------|------|
| 400 | 不正なリクエスト |
| 401 | 認証エラー |
| 403 | 権限エラー |
| 404 | リソースが見つからない |
| 429 | リクエスト制限超過 |
| 500 | サーバーエラー |

## エンドポイント

### 1. 画像解析 API

#### リクエスト
```
POST /analyze
Content-Type: multipart/form-data
```

#### パラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| file | File | ○ | 解析する画像ファイル（JPG/PNG） |
| user_id | string | × | ユーザーID（履歴保存用） |

#### レスポンス
```json
{
    "analysis_result": {
        "risk_score": 0.42,
        "risk_level": "MEDIUM",
        "confidence": 0.85
    },
    "image_quality": {
        "brightness_score": 0.95,
        "blur_score": 0.12,
        "nail_detected": true
    },
    "advice": {
        "summary": "貧血の予防のため、鉄分を意識的に摂取することをお勧めします",
        "iron_rich_foods": [
            "ほうれん草",
            "レバー",
            "牛肉",
            "あさり",
            "納豆"
        ],
        "meal_suggestions": [
            "レバニラ炒め",
            "ほうれん草の胡麻和え",
            "あさりの酒蒸し"
        ],
        "lifestyle_tips": [
            "ビタミンCを含む食品と一緒に摂取する",
            "お茶は食事の30分前後を避ける",
            "規則正しい食生活を心がける"
        ]
    },
    "warnings": [
        "画像がやや不鮮明です",
        "爪の検出精度が低い可能性があります"
    ],
    "timestamp": "2024-03-20T12:34:56.789Z"
}
```

### 2. ヘルスチェック API

#### リクエスト
```
GET /health
```

#### レスポンス
```json
{
    "status": "healthy",
    "timestamp": "2024-03-20T12:34:56.789Z",
    "version": "1.0.0",
    "services": {
        "vision_ai": "ok",
        "gemini": "ok",
        "firebase": "ok"
    }
}
```

### 3. 解析履歴取得 API

#### リクエスト
```
GET /history/{user_id}
```

#### パラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| user_id | string | ○ | ユーザーID |
| limit | integer | × | 取得件数（デフォルト: 10） |
| offset | integer | × | 開始位置（デフォルト: 0） |

#### レスポンス
```json
{
    "history": [
        {
            "id": "analysis_123",
            "timestamp": "2024-03-20T12:34:56.789Z",
            "risk_score": 0.42,
            "risk_level": "MEDIUM",
            "image_url": "https://storage.googleapis.com/...",
            "summary": "貧血の予防のため、鉄分を意識的に摂取することをお勧めします"
        }
    ],
    "pagination": {
        "total": 42,
        "limit": 10,
        "offset": 0,
        "has_more": true
    }
}
```

## レート制限

### 制限値
- 認証なし: 10 リクエスト/分
- 認証あり: 100 リクエスト/分

### レート制限ヘッダー
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1621436800
```

## バッチ処理 API

### 1. 画像一括解析 API

#### リクエスト
```
POST /batch/analyze
Content-Type: multipart/form-data
```

#### パラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| files[] | File[] | ○ | 解析する画像ファイル（最大10件） |
| user_id | string | × | ユーザーID |

#### レスポンス
```json
{
    "batch_id": "batch_123",
    "total_files": 3,
    "processed": 3,
    "results": [
        {
            "file_name": "image1.jpg",
            "status": "success",
            "result": { /* 解析結果 */ }
        },
        {
            "file_name": "image2.jpg",
            "status": "error",
            "error": "画像が不鮮明です"
        }
    ]
}
```

## WebSocket API

### 1. リアルタイム解析状況

#### 接続
```
WS /ws/analysis/{analysis_id}
```

#### メッセージフォーマット
```json
{
    "type": "progress",
    "data": {
        "step": "vision_analysis",
        "progress": 45,
        "message": "画像解析中..."
    }
}
```

## 開発者向け情報

### テスト用エンドポイント
開発環境でのみ利用可能な特別なエンドポイント：

```
POST /dev/mock-analyze
GET /dev/reset-rate-limit
```

### APIバージョニング
- URLパスによるバージョニング（例: `/v1/analyze`）
- 現在のバージョン: v1
- 非推奨バージョンの通知: `X-API-Deprecated: true`

### CORS設定
```python
origins = [
    "http://localhost:3000",
    "https://hemoglobin-guardian.web.app"
]
``` 