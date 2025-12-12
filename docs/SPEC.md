# 📘 AIまう プロジェクト仕様書

## 1. システムアーキテクチャ
**トリプルハイブリッド構成 & インメモリ分析基盤**
APIの枯渇を防ぐフェイルセーフと、高度な質問に答えるための分析基盤を兼ね備えています。

```mermaid
graph LR
    %% --- スタイル定義 ---
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef user fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef bot fill:#d1c4e9,stroke:#512da8,stroke-width:2px,color:#311b92;
    classDef logicGroup fill:#fffde7,stroke:#fbc02d,stroke-width:2px,color:#f57f17,stroke-dasharray: 5 5;
    classDef ai fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
    classDef db fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:#e65100,shape:cylinder;
    classDef external fill:#eceff1,stroke:#78909c,stroke-width:2px,color:#37474f;
    classDef monitor fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px,color:#b71c1c;
    classDef errorNote fill:#ff5252,stroke:#d50000,color:#fff,font-weight:bold,stroke-width:2px;

    %% --- ノード定義 ---
    User("👤 ユーザー"):::user
    Discord("💬 Discord"):::external
    UptimeRobot("⏱️ UptimeRobot<br>(死活監視)"):::monitor
    
    %% Renderホスティング環境
    subgraph RenderHost ["☁️ Render ホスティング環境 (Free Plan)"]
        Bot("🤖 AIまう<br>(Bot 本体)"):::bot
        Worker("🔄 Scheduler Worker<br>(定期実行タスク)"):::bot
        Analytics("🧠 Analytics Service<br>(分析モジュール)"):::bot
        SQLite[("📊 In-Memory SQLite<br>(一時DB)")]:::db
    end

    %% 外部AIサービス群
    subgraph AI_Services ["🧠 AI 推論API群 (Free Plan)"]
        GeminiMain("Google AI Studio<br>Gemini 2.5 Flash"):::ai
        GeminiSub("Google AI Studio<br>Gemini 2.5 Flash Lite"):::ai
        GroqAI("Groq Cloud<br>Llama 3.3"):::ai
        GroqWorker("Groq Cloud<br>Llama 3"):::ai
    end

    %% 外部データベース・他サービス
    DB[("🗄️ Supabase<br>(PostgreSQL DB)")]:::db
    TimeTree("📅 TimeTree<br>(外部カレンダー)"):::external

    %% --- フロー接続 ---
    
    %% 監視
    UptimeRobot -.-> RenderHost

    %% メインエントリー
    User --> Discord --> Bot

    %% === ロジックフロー ===

    %% 1. 通常会話ロジック
    subgraph Logic_Brain ["🗣️ 通常会話ロジック (AI Brain)"]
        Bot -->|"① 会話要求"| GeminiMain
        GeminiMain -.->|"② エラー/制限時"| GeminiSub
        GeminiSub -.->|"③ エラー/制限時"| GroqAI
    end

    %% 2. データ分析ロジック
    subgraph Logic_Analysis ["📈 データ分析ロジック (High-IQ)"]
        Bot -->|"①「分析して」等"| Analytics
        Analytics -->|"② データロード"| DB
        Analytics -->|"③ 一時DB作成"| SQLite
        Analytics -->|"④ SQL生成要求"| GeminiMain
        GeminiMain -->|"⑤ SQL実行"| SQLite
        SQLite -->|"⑥ 結果データ返却"| Bot
    end

    %% 3. データ同期ロジック
    subgraph Logic_Sync ["🔄 データ同期ロジック (定期実行)"]
        TimeTree -->|"① スクレイピング"| Worker
        Worker -->|"② AI解析要求"| GroqWorker
        GroqWorker -->|"③ 構造化データ保存"| DB
    end

    %% サブグラフのスタイル適用
    class Logic_Brain,Logic_Analysis,Logic_Sync logicGroup;
```

## 2. 会話・挙動ロジック

### 🧠 記憶と文脈

  * **履歴参照:** 直近 **10件** の会話ログをプロンプトに含めて送信します。
  * **文字数制限:** 返答は原則 **200文字以内** で、Twitterのリプライのようにテンポよく返します。
    * **例外:** ライブ情報の告知やスケジュール詳細を伝える場合は、情報量を優先し、文字数制限を無視して詳細に答えます。
  * **特典強調:** イベントに特典（Bonus）がある場合は、絵文字をつけて優先的にアピールします。

### 📊 高IQ分析機能 (High-IQ Analytics)

ユーザーからの高度な質問（例：「今月のライブ数は？」「次の予定は？」）に対して、以下のフローで回答します。

1.  **インメモリDB構築**: Supabaseから最新のスケジュールを取得し、メモリ上のSQLiteに展開（5分間キャッシュ）。
2.  **SQL生成**: Geminiが質問内容から SQLクエリ (`SELECT ...`) を生成。
    * **詳細優先**: スケジュール照会時は `place`, `price_details`, `ticket_url`, `bonus` を積極的に取得。
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

| ディレクトリ   | ファイル名             | 役割                                         |
| :------------- | :--------------------- | :------------------------------------------- |
| `src/app/`     | `main.py`              | エントリーポイント。                         |
|                | `bot.py`               | Discord Bot本体。メッセージ受信・応答制御。  |
|                | `server.py`            | UptimeRobot用サーバー (Keep-Alive)。         |
| `src/domain/`  | `ai_service.py`        | AI推論ロジック (Gemini / Groq)。             |
|                | `analytics_service.py` | **(New)** AIによるSQL分析・実行サービス。    |
|                | `persona.py`           | AIへのシステムプロンプト定義。               |
| `src/workers/` | `scheduler.py`         | TimeTree同期ワーカー（AI補正・DryRun対応）。 |
|                | `fetcher.py`           | 過去ログ取得用スクリプト。                   |
| `src/core/`    | `config.py`            | 環境変数と定数管理。                         |
|                | `logger.py`            | ロギング設定。                               |

## 4. 管理情報 (Service Stack)

| サービス             | 用途             | プラン |
| :------------------- | :--------------- | :----- |
| **Render**           | ホスティング     | Free   |
| **UptimeRobot**      | 死活監視         | Free   |
| **Supabase**         | データベース     | Free   |
| **Google AI Studio** | AI推論 (Gemini)  | Free   |
| **Groq Cloud**       | AI推論 (Llama 3) | Free   |

## 5. データベース設計 (Supabase)

### `schedules` テーブル

  - `source_id` (PK): TimeTreeイベントID
  - `title`: イベント名
  - `start_at`: 開始日時 (ISO 8601)
  - `end_at`: 終了日時
  - `description`: 詳細メモ
  - `place`: 会場・場所
  - `ticket_url`: チケット購入URL
  - `price_details`: 料金詳細
  - `bonus`: 入場特典
