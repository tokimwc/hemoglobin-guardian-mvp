# ヘモグロビンガーディアン API仕様書

## 概要

貧血リスクを推定し、AIアドバイスを提供するバックエンドAPI

- ベースURL: `http://localhost:8080` (開発環境)
- 認証: なし (MVP版)

## エンドポイント

### 1. ヘルスチェック

```
GET /health
```

システムの稼働状態を確認します。

#### レスポンス

```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

### 2. 画像解析

```
POST /analyze
```

爪の画像を解析し、貧血リスクを推定します。

#### リクエスト

- Content-Type: `multipart/form-data`

| パラメータ | 型 | 必須 | 説明 |
|------------|-------|--------|----------|
| file | File | ○ | 爪の画像ファイル (JPEG/PNG) |
| user_id | string | × | ユーザーID（履歴保存時に必要） |

#### レスポンス

```json
{
    "risk_score": 0.5,
    "risk_level": "MEDIUM",
    "confidence_score": 0.8,
    "warnings": [
        "画像がブレています"
    ],
    "quality_metrics": {
        "is_blurry": true,
        "brightness_score": 0.7,
        "has_proper_lighting": true,
        "has_detected_nail": true
    },
    "advice": {
        "summary": "鉄分を意識的に摂取することをおすすめします",
        "iron_rich_foods": [
            "レバー",
            "ほうれん草",
            "牡蠣"
        ],
        "meal_suggestions": [
            "レバーとほうれん草の炒め物"
        ],
        "lifestyle_tips": [
            "規則正しい食事を心がけましょう"
        ]
    },
    "created_at": "2024-01-15T12:34:56.789Z"
}
```

#### エラーレスポンス

```json
{
    "detail": "画像解析中にエラーが発生しました: ..."
}
```

### 3. 解析履歴取得

```
GET /history/{user_id}
```

ユーザーの解析履歴を取得します。

#### パラメータ

| パラメータ | 型 | 必須 | 説明 |
|------------|-------|--------|----------|
| user_id | string | ○ | ユーザーID |
| limit | integer | × | 取得件数 (デフォルト: 10) |

#### レスポンス

```json
[
    {
        "history_id": "abc123",
        "user_id": "user123",
        "analysis_result": {
            // 解析結果（上記の解析レスポンスと同じ形式）
        }
    }
]
```

## エラーコード

| ステータスコード | 説明 |
|-----------------|------|
| 200 | 成功 |
| 422 | バリデーションエラー |
| 500 | サーバーエラー |

## 注意事項

1. 画像品質について
   - ブレのない鮮明な画像を使用
   - 適切な明るさでの撮影
   - 爪全体が写るように撮影

2. 解析結果について
   - リスクスコアは参考値です
   - 医療診断の代替とはなりません
   - 信頼度スコアが低い場合は再撮影を推奨 