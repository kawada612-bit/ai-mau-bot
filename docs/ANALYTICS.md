# Analytics Guide

AI Mau Botのアナリティクス機能（Google Analytics 4 + ログ分析）の設定・使用方法です。

## 1. Google Analytics 4 (GA4)

フロントエンド（Next.js）でのユーザー行動分析に使用します。

### 設定方法

1. [Google Analytics](https://analytics.google.com/)でプロパティを作成し、測定ID (`G-XXXXXXXXXX`) を取得。
2. `frontend/.env.local` に設定:
   ```env
   NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
   ```

### 追跡されるイベント

| イベント名             | トリガー           | パラメータ                                                   |
| ---------------------- | ------------------ | ------------------------------------------------------------ |
| `chat_message_sent`    | メッセージ送信時   | `user_name` (ユーザー名), `message_length` (文字数)          |
| `ai_response_received` | AIからの応答受信時 | `response_length` (応答文字数), `response_time` (応答時間秒) |
| `chat_error`           | エラー発生時       | `error_message` (エラー内容)                                 |

---

## 2. ログベース分析 (Log-based)

バックエンド（FastAPI）のパフォーマンス分析と技術的な詳細確認に使用します。

### ログの仕様
`server.py` は標準ログに加えて、以下のJSON形式の構造化ログを出力します：

```json
ANALYTICS: {
    "timestamp": "2023-10-27T10:00:00.000000",
    "event": "chat_request",
    "ip": "127.0.0.1",
    "user_name": "Guest",
    "message_length": 15,
    "response_time": 1.234,
    "success": true,
    "error": null
}
```

### 解析ツールの使用方法

`scripts/analyze_logs.py` を使用して、ログファイルから統計レポートを生成できます。

```bash
# ログファイルを解析
python scripts/analyze_logs.py logs/app.log
```

### 出力レポート例

```
📊 AI Mau Bot Analytics Report
==================================================

📈 Traffic Overview
Total Requests: 15
Success Rate:   15/15 (100.0%)
Unique Users:   2

⏱️ Performance
Avg Response Time: 3.120s
Max Response Time: 5.430s
Min Response Time: 1.200s

🤖 AI Model Usage
- Groq Llama 3: 12 (80.0%)
- Gemini 2.5: 3 (20.0%)

❌ Error Analysis
No errors recorded! 🎉
```
