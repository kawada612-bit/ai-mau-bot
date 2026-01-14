# 🤖 AIまう (AI Mau Bot)

実在するアイドルのデータを基に、その人格（口調・性格・リスペクト）を模倣して会話する Discord Bot + Web チャットアプリケーションです。

Google の生成AI「Gemini 3 Flash Preview」を筆頭に、5つのモデルをフォールバック構成で搭載。
API制限やサーバーダウン時でも会話を継続できる、極めて高い可用性を実現しています。

## ✨ 主な機能

### Discord Bot
* **なりきり会話:** 独特な挨拶（「やほす〜」）やタメ口、絵文字など、キャラクターを忠実に再現します。
* **高IQ回答:** アイドルらしさを保ちつつ、技術的な質問や計算にも的確に答えます。
* **データ分析機能:** 「今月のライブ数は?」などの質問に対して、SQLを生成してデータベースから情報を取得し回答します。
* **鉄壁の可用性:** Geminiが応答しない場合、自動でGroq (Llama 3) に切り替わり応答します。
* **空気を読む:** 特定チャンネルでは雑談に応じますが、他人へのメンションが含まれる会話には割り込みません。
* **レート制限:** 1分間に10メッセージまでの制限を設け、APIの乱用を防ぎます。

### Web チャットアプリ
* **リアルタイム会話:** Next.js製のモダンなUIで、ブラウザから直接AIまうと会話できます。
* **会話履歴の永続化:** LocalStorageを使用して、ページをリロードしても会話が保持されます。
* **ユーザー名のカスタマイズ:** 初回アクセス時に名前を設定し、以降はその名前で呼ばれます。
* **リッチリンクカード:** URLが含まれるメッセージでは、OGP（Open Graph Protocol）を使用してリッチなカードを表示します。
* **PWA対応 (NEW):** スマートフォンのホーム画面に追加して、ネイティブアプリのように使用できます。
* **動的サジェスト機能:** AIが文脈に合わせて「次に言いそうなこと」を3つ提案し、ワンタップで返信できます。

## 🛠️ 使用技術

### Backend
* **言語:** Python 3.10+
* **フレームワーク:** `discord.py`, `FastAPI`
* **AIモデル (本番環境優先順):**
    1. Google Gemini 3 Flash Preview (最新・最高性能)
    2. Google Gemini 2.5 Flash (高性能)
    3. Google Gemini 2.5 Flash Lite (Free Tier)
    4. Google Gemini 2.0 Flash Exp (Search連携)
    5. Google Gemma 3 27B (バックアップ)
* **開発環境:** Gemma 3 → 2.5 Lite → 2.5 Flash → 3 Flash → 2.0 Flash Exp (コスト節約優先)
* **データベース:** Supabase (PostgreSQL)
* **スケジューラー:** TimeTree連携による自動データ同期

### Frontend
* **フレームワーク:** Next.js 16 (App Router)
* **スタイリング:** Tailwind CSS + Custom CSS
* **アニメーション:** Framer Motion
* **状態管理:** React Hooks + LocalStorage
* **分析:** Google Analytics 4 (GA4)

### インフラ
* **ホスティング:** Render (Web Service)
* **監視:** UptimeRobot (常時稼働監視)

## 🚀 セットアップ手順

### 1. 環境変数の設定
`.env` ファイルを作成し、以下の情報を設定してください。

| 変数名              | 説明                 | 取得方法                 |
| :------------------ | :------------------- | :----------------------- |
| `DISCORD_TOKEN`     | Botトークン          | Discord Developer Portal |
| `GEMINI_API_KEY`    | メインAI用キー       | Google AI Studio         |
| `GROQ_API_KEY`      | バックアップAI用キー | Groq Console             |
| `TARGET_CHANNEL_ID` | 雑談用チャンネルID   | Discord (開発者モード)   |
| `SUPABASE_URL`      | データベースURL      | Supabase Dashboard       |
| `SUPABASE_KEY`      | データベースキー     | Supabase Dashboard       |

### 2. バックエンドのセットアップ

#### Mac / Linux
```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# インストール & 起動
pip install -r requirements.txt
./run_dev.sh
```

#### Windows
```cmd
:: 仮想環境作成
python -m venv venv
.\\venv\\Scripts\\activate

:: インストール & 起動
pip install -r requirements.txt
.\\run_dev.bat
```

### 3. フロントエンドのセットアップ

```bash
cd frontend

# 環境変数設定
# .env.local ファイルを作成し、以下を設定
# NEXT_PUBLIC_API_URL=http://localhost:8000

# インストール & 起動
npm install
npm run dev
```

ブラウザで `http://localhost:3000` にアクセスすると、チャットUIが表示されます。

## 🚀 デプロイ

本番環境へのデプロイ手順は、[デプロイワークフロー](.agent/workflows/deploy.md)を参照してください。

### 概要
- **バックエンド**: Render Web Service (FastAPI + Discord Bot)
- **フロントエンド**: Vercel (Next.js)
- **スリープ対策**: 自己Ping機能内蔵（14分ごとに自動アクセス）

詳細な手順、環境変数の設定、CORS設定、トラブルシューティングについては、デプロイワークフローをご確認ください。

## 📁 プロジェクト構成

```
ai-mau-bot/
├── src/                      # バックエンドソースコード
│   ├── app/                  # アプリケーション層
│   │   ├── bot.py           # Discord Bot本体
│   │   ├── server.py        # FastAPI サーバー
│   │   └── main.py          # エントリーポイント
│   ├── domain/              # ドメイン層
│   │   ├── ai_service.py    # AI推論ロジック
│   │   ├── analytics_service.py  # データ分析サービス
│   │   └── persona.py       # AIプロンプト定義
│   ├── services/            # サービス層
│   │   └── ogp_service.py   # OGPメタデータ取得
│   ├── workers/             # バックグラウンドワーカー
│   │   └── scheduler.py     # TimeTree同期ワーカー
│   └── core/                # コア機能
│       ├── config.py        # 環境変数管理
│       └── logger.py        # ロギング設定
├── frontend/                # フロントエンドソースコード
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # Reactコンポーネント
│   │   ├── hooks/          # カスタムフック
│   │   └── lib/            # ユーティリティ
│   └── public/             # 静的ファイル
├── docs/                   # ドキュメント
│   ├── SPEC.md            # 技術仕様書
│   ├── CONTRIBUTING.md    # 開発ガイド
│   └── BACKLOG.md         # 開発バックログ
└── requirements.txt       # Python依存関係
```

## 🤝 開発について

このプロジェクトは **Git Flow Lite** を採用しています。
*   `main`: 本番環境 (自動デプロイ)
*   `develop`: 開発用ブランチ

詳細は [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) をご覧ください。

## 🤖 開発ツールについて

このプロジェクトは、AIネイティブエディタ **Google Antigravity** を使用して開発されています。
ディレクトリ構成やタスク管理は、エージェント主導開発 (Agent-Driven Development) を前提としています。

## 📄 ドキュメント

より詳細な仕様や内部ロジックについては以下のドキュメントを参照してください：

* [SPEC.md](docs/SPEC.md) - 技術仕様書
* [CONTRIBUTING.md](docs/CONTRIBUTING.md) - 開発ガイド
* [BACKLOG.md](docs/BACKLOG.md) - 開発バックログ
* [frontend/README.md](frontend/README.md) - フロントエンド詳細

## 📝 ライセンス

MIT License