# 📘 AIまう プロジェクト仕様書

## 1. システムアーキテクチャ
**トリプルハイブリッド構成 (Triple Hybrid Failover)**
APIの枯渇やサーバーエラーを防ぐため、3段階のフェイルセーフを実装しています。

```mermaid
graph TD
    User[ユーザー] -->|Discord| Bot[AIまう]
    
    subgraph "AI Brain Logic"
        Bot -->|優先 1| GeminiMain[Gemini 2.5 Flash]
        GeminiMain -.->|Error/Limit| GeminiSub[Gemini 2.5 Flash Lite]
        GeminiSub -.->|Error/Limit| Groq[Groq (Llama 3.3)]
    end
    
    GeminiSub -->|成功時| Note1[末尾に ※省エネモード を付与]
    Groq -->|成功時| Note2[末尾に ※規制モード を付与]

    subgraph "Data Sync Logic"
        TimeTree[TimeTree (External)] -->|Scraping| Worker[Sync Worker (Playwright)]
        Worker -->|AI Parsing| GroqWorker[Groq (Llama 3)]
        GroqWorker -->|Structured Data| DB[(Supabase)]
        DB -->|RAG / Live Info| Bot
    end
```

## 2. 会話・挙動ロジック

### 🧠 記憶と文脈

  * **履歴参照:** 直近 **10件** の会話ログをプロンプトに含めて送信します。
  * **文字数制限:** 返答は原則 **200文字以内** で、Twitterのリプライのようにテンポよく返します。
  * **長文対応:** 生成された回答が2000文字を超えた場合、自動的に分割して連投します。

### 🛡️ 応答トリガー (空気を読む機能)

`on_message` イベントにて以下の優先順位で判定します。

1.  **メンションされた場合 (`@AIまう`)**
      * → 無条件で反応します。
2.  **指定チャンネル (`TARGET_CHANNEL_ID`) の場合**
      * 自分以外のユーザーへのメンションが含まれている場合 (`@田中` など)
          * → **無視します** (会話に割り込まない)。
      * 誰へのメンションもない場合 (独り言・全体チャット)
          * → **反応します** (雑談として処理)。
3.  **それ以外**
      * → 無視します。

## 3. ファイル構成

| ファイル名 | 役割 |
| :--- | :--- |
| `src/main.py` | ボットのメインプログラム。Discord接続、AI呼び出しロジック。 |
| `src/server.py` | UptimeRobot用サーバー (Keep-Alive)。 |
| `src/sync_schedule.py` | TimeTree同期・AI整形・DB保存を行うワーカー。 |
| `src/config.py` | 環境変数と定数管理。 |
| `src/ai/persona.py` | AIへのシステムプロンプト（人格定義、Wiki情報、会話ルール）。 |
| `src/ai/core.py` | AI推論ロジック (Gemini / Groq)。 |
| `src/check_timetree.py` | (診断用) TimeTree接続テスト。 |
| `requirements.txt` | 依存ライブラリ一覧。Renderのデプロイ時に使用。 |
| `BACKLOG.md` | 機能追加やバグ修正のタスク管理表。 |

## 4. 管理情報 (Service Stack)

| サービス | 用途 | プラン |
| :--- | :--- | :--- |
| **Render** | ホスティング (Web Service) | Free (15分スリープあり) |
| **UptimeRobot** | 死活監視 (Keep-Alive) | Free (5分間隔) |
| **Supabase** | データベース (PostgreSQL) | Free |
| **Google AI Studio** | AI推論 (Gemini) | Free |
| **Groq Cloud** | AI推論 (Llama 3) | Free |

## 5. データベース設計

**Supabase (PostgreSQL)**

### `schedules` テーブル
TimeTreeから同期したイベント情報を格納します。
- `source_id` (PK): TimeTreeのイベントID
- `title`: イベント名
- `start_at`: 開始日時 (ISO 8601)
- `end_at`: 終了日時
- `description`: 詳細メモ
- `updated_at`: 情報更新日時

### `x_posts` テーブル
X (旧Twitter) のポストをアーカイブします。（今後実装予定）
