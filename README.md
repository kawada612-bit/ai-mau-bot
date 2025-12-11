# 🤖 AIまう (Discord Bot)

実在するアイドルのデータを基に、その人格（口調・性格・リスペクト）を模倣して会話する Discord ボットです。

Google の生成AI「Gemini 2.5 Flash」を主軸に、予備の「Gemini 2.5 Flash Lite」、さらに最終手段として「Groq (Llama 3)」を搭載した**トリプルハイブリッド構成**を採用。
API制限やサーバーダウン時でも会話を継続できる、極めて高い可用性を実現しています。

## ✨ 主な機能

* **なりきり会話:** 独特な挨拶（「やほす〜」）やタメ口、絵文字など、キャラクターを忠実に再現します。
* **高IQ回答:** アイドルらしさを保ちつつ、技術的な質問や計算にも的確に答えます。
* **鉄壁の可用性:** Geminiが応答しない場合、自動でGroq (Llama 3) に切り替わり応答します。
* **空気を読む:** 特定チャンネルでは雑談に応じますが、他人へのメンションが含まれる会話には割り込みません。

## 🛠️ 使用技術

* **言語:** Python 3.10+
* **フレームワーク:** `discord.py`, `Flask` (Webサーバー用)
* **AIモデル:**
    * Main: Google Gemini 2.5 Flash
    * Sub: Google Gemini 2.5 Flash Lite
    * Fallback: Groq (Llama 3.3)
* **インフラ:** Render (Web Service) + UptimeRobot (常時稼働監視)

## 🚀 セットアップ手順 (ローカル実行)

### 1. 必要な環境変数の設定
`.env` ファイルを作成し、以下の情報を設定してください。

| 変数名 | 説明 | 取得方法 |
| :--- | :--- | :--- |
| `DISCORD_TOKEN` | Botトークン | Discord Developer Portal |
| `GEMINI_API_KEY` | メインAI用キー | Google AI Studio |
| `GROQ_API_KEY` | バックアップAI用キー | Groq Console |
| `TARGET_CHANNEL_ID` | 雑談用チャンネルID | Discord (開発者モード) |

### 2. インストール & 起動

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
.\venv\Scripts\activate

:: インストール & 起動
pip install -r requirements.txt
.\run_dev.bat
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

より詳細な仕様や内部ロジックについては [SPEC.md](SPEC.md) を参照してください。