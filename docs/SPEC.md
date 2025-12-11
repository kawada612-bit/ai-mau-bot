# 📘 AIまう プロジェクト仕様書

## 1. システムアーキテクチャ
**トリプルハイブリッド構成 & インメモリ分析基盤**
APIの枯渇を防ぐフェイルセーフと、高度な質問に答えるための分析基盤を兼ね備えています。

```mermaid
graph TD
    User[ユーザー] -->|Discord| Bot[AIまう]
    
    subgraph "AI Brain Logic"
        Bot -->|会話| GeminiMain[Gemini 2.5 Flash]
        GeminiMain -.->|Error/Limit| GeminiSub[Gemini 2.5 Flash Lite]
        GeminiSub -.->|Error/Limit| Groq[Groq (Llama 3.3)]
    end
    
    subgraph "Data Analysis Logic (High-IQ)"
        Bot -->|「分析して」「いつ？」| Analytics[Analytics Service]
        Analytics -->|Load Data| DB[(Supabase)]
        Analytics -->|Create| SQLite[In-Memory SQLite]
        Analytics -->|Generate SQL| GeminiMain
        GeminiMain -->|SQL Query| SQLite
        SQLite -->|Table Data| Bot
    end

    subgraph "Data Sync Logic"
        TimeTree[TimeTree (External)] -->|Scraping| Worker[Scheduler Worker]
        Worker -->|AI Parsing| GroqWorker[Groq (Llama 3)]
        GroqWorker -->|Structured Data| DB
    end
```

## 2. 会話・挙動ロジック

### 🧠 記憶と文脈

  * **履歴参照:** 直近 **10件** の会話ログをプロンプトに含めて送信します。
  * **文字数制限:** 返答は原則 **200文字以内** で、Twitterのリプライのようにテンポよく返します。
  * **長文対応:** 生成された回答が2000文字を超えた場合、自動的に分割して連投します。

### 📊 高IQ分析機能 (High-IQ Analytics)

ユーザーからの高度な質問（例：「今月のライブ数は？」「次の予定は？」）に対して、以下のフローで回答します。

1.  **インメモリDB構築**: Supabaseから最新のスケジュールを取得し、メモリ上のSQLiteに展開（5分間キャッシュ）。
2.  **SQL生成**: Geminiが質問内容から SQLクエリ (`SELECT ...`) を生成。
3.  **実行**: 生成されたSQLをSQLiteで安全に実行。
4.  **回答**: 実行結果（表データ）を基に、まうちゃんの人格で回答を生成。

### 🛡️ 応答トリガー (空気を読む機能)

`on_message` イベントにて以下の優先順位で判定します。

1.  **メンションされた場合 (`@AIまう`)**: 無条件で反応。
2.  **指定チャンネル**:
      - 他人へのメンションがある → 無視。
      - 独り言・全体チャット → 反応。
3.  **それ以外**: 無視。

## 3. ファイル構成 (Modular Monolith)

| ディレクトリ | ファイル名 | 役割 |
| :--- | :--- | :--- |
| `src/app/` | `main.py` | エントリーポイント。 |
| | `bot.py` | Discord Bot本体。メッセージ受信・応答制御。 |
| | `server.py` | UptimeRobot用サーバー (Keep-Alive)。 |
| `src/domain/` | `ai_service.py` | AI推論ロジック (Gemini / Groq)。 |
| | `analytics_service.py` | **(New)** AIによるSQL分析・実行サービス。 |
| | `persona.py` | AIへのシステムプロンプト定義。 |
| `src/workers/` | `scheduler.py` | TimeTree同期ワーカー（AI補正・DryRun対応）。 |
| | `fetcher.py` | 過去ログ取得用スクリプト。 |
| `src/core/` | `config.py` | 環境変数と定数管理。 |
| | `logger.py` | ロギング設定。 |

## 4. 管理情報 (Service Stack)

| サービス | 用途 | プラン |
| :--- | :--- | :--- |
| **Render** | ホスティング | Free |
| **UptimeRobot** | 死活監視 | Free |
| **Supabase** | データベース | Free |
| **Google AI Studio** | AI推論 (Gemini) | Free |
| **Groq Cloud** | AI推論 (Llama 3) | Free |

## 5. データベース設計 (Supabase)

### `schedules` テーブル

  - `source_id` (PK): TimeTreeイベントID
  - `title`: イベント名
  - `start_at`: 開始日時 (ISO 8601)
  - `end_at`: 終了日時
  - `description`: 詳細メモ
