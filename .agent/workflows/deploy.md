---
description: Render + Vercelへのデプロイ手順
---

# 🚀 Render + Vercelへのデプロイ手順

このプロジェクトは以下の2つのコンポーネントで構成されています：
- **バックエンド**: FastAPI + Discord Bot (Python) → **Render**
- **フロントエンド**: Next.js (React) → **Vercel**

---

## 📋 事前準備

### 1. アカウントの作成
- [Render](https://render.com/) - バックエンド用
- [Vercel](https://vercel.com/) - フロントエンド用

両方ともGitHubアカウントでサインアップできます。

### 2. リポジトリの準備
GitHubにプロジェクトをプッシュしておきます：
```bash
git add .
git commit -m "デプロイ準備完了"
git push origin main
```

### 3. 環境変数の確認
デプロイ前に、以下の環境変数が `.env` ファイルに設定されていることを確認してください：

**バックエンド用:**
- `DISCORD_TOKEN`: Discord Botトークン
- `GEMINI_API_KEY`: Google AI Studio APIキー
- `GROQ_API_KEY`: Groq Cloud APIキー
- `TARGET_CHANNEL_ID`: Discord対象チャンネルID
- `SUPABASE_URL`: Supabase データベースURL
- `SUPABASE_KEY`: Supabase APIキー
- `TIMETREE_CALENDAR_ID`: TimeTreeカレンダーID (スケジューラー使用時)
- `TIMETREE_TOKEN`: TimeTree APIトークン (スケジューラー使用時)
- `ALLOWED_ORIGINS`: CORS許可オリジン (後で設定)

**フロントエンド用:**
- `NEXT_PUBLIC_API_URL`: バックエンドAPIのURL (デプロイ後に設定)

---

## 🔧 Part 1: バックエンドのデプロイ (Render)

### ステップ 1: Render Dashboardにアクセス
1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. 右上の **"New +"** ボタンをクリック
3. **"Web Service"** を選択

### ステップ 2: リポジトリの接続
1. **"Connect a repository"** セクションで、GitHubリポジトリを選択
2. `ai-mau-bot` リポジトリを選択
3. **"Connect"** をクリック

### ステップ 3: サービスの設定
以下の設定を入力してください：

| 項目               | 設定値                                 |
| ------------------ | -------------------------------------- |
| **Name**           | `ai-mau-bot-backend` (任意の名前)      |
| **Region**         | `Singapore` (または最寄りのリージョン) |
| **Branch**         | `main`                                 |
| **Root Directory** | (空欄のまま)                           |
| **Runtime**        | `Python 3`                             |
| **Build Command**  | `pip install -r requirements.txt`      |
| **Start Command**  | `python -m src.app.main`               |
| **Instance Type**  | `Free`                                 |

### ステップ 4: 環境変数の設定（一時的）
まず、CORS設定以外の環境変数を追加します：

```
DISCORD_TOKEN=<Discord Botトークン>
GEMINI_API_KEY=<Google AI Studio APIキー>
GROQ_API_KEY=<Groq Cloud APIキー>
TARGET_CHANNEL_ID=<Discord対象チャンネルID>
SUPABASE_URL=<Supabase データベースURL>
SUPABASE_KEY=<Supabase APIキー>
TIMETREE_CALENDAR_ID=<TimeTreeカレンダーID>
TIMETREE_TOKEN=<TimeTree APIトークン>
```

> **注意**: `ALLOWED_ORIGINS` は後でVercelのURLが確定してから追加します。

### ステップ 5: デプロイの実行
1. **"Create Web Service"** ボタンをクリック
2. デプロイが開始されます（初回は5〜10分程度かかります）
3. ログを確認し、エラーがないことを確認

### ステップ 6: バックエンドURLの確認
1. デプロイが完了したら、Render Dashboardの上部に表示される **URL** をコピー
   - 例: `https://ai-mau-bot-backend.onrender.com`
2. このURLをメモしておきます（フロントエンドで使用します）

### ステップ 7: 動作確認（一時的）
1. ブラウザで `https://ai-mau-bot-backend.onrender.com/health` にアクセス
2. `{"status": "ok"}` のようなレスポンスが返ってくることを確認
3. Discord Botが起動していることを確認
4. ログで自己Ping機能が動作していることを確認
   - `🏓 Self-ping enabled` のログが表示される
   - 14分ごとに `✅ Self-ping successful` のログが表示される

> **💡 自己Ping機能について**
> 
> バックエンドには自己Ping機能が組み込まれており、14分ごとに自分自身の `/health` エンドポイントにアクセスします。
> これにより、Renderの無料プランでもスリープせずに常時稼働します。

---

## 🎨 Part 2: フロントエンドのデプロイ (Vercel)

### ステップ 1: Vercel Dashboardにアクセス
1. [Vercel Dashboard](https://vercel.com/dashboard) にログイン
2. **"Add New..."** → **"Project"** をクリック

### ステップ 2: リポジトリのインポート
1. **"Import Git Repository"** セクションで、GitHubリポジトリを選択
2. `ai-mau-bot` リポジトリを選択
3. **"Import"** をクリック

### ステップ 3: プロジェクトの設定
以下の設定を入力してください：

| 項目                 | 設定値                             |
| -------------------- | ---------------------------------- |
| **Project Name**     | `ai-mau-bot-frontend` (任意の名前) |
| **Framework Preset** | `Next.js` (自動検出されます)       |
| **Root Directory**   | `frontend`                         |
| **Build Command**    | `npm run build` (デフォルト)       |
| **Output Directory** | `.next` (デフォルト)               |
| **Install Command**  | `npm install` (デフォルト)         |

### ステップ 4: 環境変数の設定
1. **"Environment Variables"** セクションを展開
2. 以下の環境変数を追加：

| Name                  | Value                                     |
| --------------------- | ----------------------------------------- |
| `NEXT_PUBLIC_API_URL` | `https://ai-mau-bot-backend.onrender.com` |

> **重要**: バックエンドのURLを正確に入力してください（末尾のスラッシュなし）。

### ステップ 5: デプロイの実行
1. **"Deploy"** ボタンをクリック
2. デプロイが開始されます（初回は3〜5分程度かかります）
3. ビルドログを確認し、エラーがないことを確認

### ステップ 6: フロントエンドURLの確認
1. デプロイが完了したら、**"Visit"** ボタンをクリックするか、表示されるURLをコピー
   - 例: `https://ai-mau-bot-frontend.vercel.app`
2. このURLをメモしておきます（バックエンドのCORS設定で使用します）

### ステップ 7: 動作確認
1. ブラウザで `https://ai-mau-bot-frontend.vercel.app` にアクセス
2. チャットUIが表示されることを確認
3. メッセージを送信してみる（CORS設定前なので、エラーになる可能性があります）

---

## 🔗 Part 3: CORS設定の更新

フロントエンドからバックエンドへのAPIリクエストを許可するため、バックエンドのCORS設定を更新します。

### ステップ 1: Renderに戻る
1. [Render Dashboard](https://dashboard.render.com/) に戻る
2. `ai-mau-bot-backend` サービスを選択

### ステップ 2: 環境変数を追加
1. 左メニューから **"Environment"** を選択
2. **"Add Environment Variable"** をクリック
3. 以下を追加：

| Key               | Value                                                          |
| ----------------- | -------------------------------------------------------------- |
| `ALLOWED_ORIGINS` | `https://ai-mau-bot-frontend.vercel.app,http://localhost:3000` |

> **説明**: 
> - Vercelのプロダクション URL
> - ローカル開発用URL
> - カンマ区切りで複数指定可能

### ステップ 3: 再デプロイ
1. 環境変数を保存すると、自動的に再デプロイが開始されます
2. 再デプロイ完了まで待ちます（1〜2分程度）

### ステップ 4: 最終動作確認
1. フロントエンド (`https://ai-mau-bot-frontend.vercel.app`) にアクセス
2. メッセージを送信し、AIからの返答があることを確認
3. URLを含むメッセージでOGPカードが表示されることを確認
4. LocalStorageで会話履歴が保存されることを確認

---

## 🔄 Part 4: 継続的デプロイの設定

### Vercel (フロントエンド)
Vercelは、GitHubリポジトリの `main` ブランチにプッシュすると自動的に再デプロイされます。

**自動デプロイの流れ:**
1. ローカルで変更をコミット
   ```bash
   git add .
   git commit -m "機能追加: XXX"
   git push origin main
   ```
2. Vercelが自動的に変更を検知
3. 自動的にビルド＆デプロイが実行される
4. 1〜2分後に本番環境に反映される

### Render (バックエンド)
Renderも同様に、`main` ブランチへのプッシュで自動再デプロイされます。

---

## 🛡️ Part 5: UptimeRobotの設定（オプション）

> **💡 注意**: バックエンドには自己Ping機能が組み込まれているため、UptimeRobotの設定は**オプション**です。
> 
> 自己Ping機能だけでもスリープを防げますが、以下の理由でUptimeRobotの併用を推奨します：
> - **冗長性**: 自己Ping機能が何らかの理由で失敗した場合のバックアップ
> - **監視**: サービスのダウンタイムをメールで通知
> - **統計**: 稼働率やレスポンスタイムの記録

### ステップ 1: UptimeRobotアカウントの作成
1. [UptimeRobot](https://uptimerobot.com/) にアクセス
2. 無料アカウントを作成

### ステップ 2: モニターの追加
1. **"Add New Monitor"** をクリック
2. 以下の設定を入力：

| 項目                    | 設定値                                           |
| ----------------------- | ------------------------------------------------ |
| **Monitor Type**        | `HTTP(s)`                                        |
| **Friendly Name**       | `AI Mau Bot Backend`                             |
| **URL**                 | `https://ai-mau-bot-backend.onrender.com/health` |
| **Monitoring Interval** | `5 minutes`                                      |

3. **"Create Monitor"** をクリック

---

## 📊 Part 6: デプロイ後の確認チェックリスト

### バックエンド (Render)
- [ ] `/health` エンドポイントが正常に応答する
- [ ] Discord Botがオンライン状態になっている
- [ ] Discordでメンションして返答がある
- [ ] ログにエラーが出ていない
- [ ] 自己Ping機能が動作している

### フロントエンド (Vercel)
- [ ] チャットUIが正しく表示される
- [ ] メッセージ送信が機能する
- [ ] AIからの返答が表示される
- [ ] LocalStorageで会話履歴が保存される
- [ ] URLを含むメッセージでOGPカードが表示される

### 連携
- [ ] CORS設定が正しく機能している
- [ ] フロントエンドからバックエンドへのAPI通信が成功する

---

## 🐛 トラブルシューティング

### バックエンドが起動しない
1. Renderのログを確認
2. 環境変数が正しく設定されているか確認
3. `requirements.txt` に必要なパッケージが全て含まれているか確認

### フロントエンドがビルドエラー
1. Vercelのビルドログを確認
2. `Root Directory` が `frontend` に設定されているか確認
3. 環境変数 `NEXT_PUBLIC_API_URL` が設定されているか確認

### Discord Botが応答しない
1. `DISCORD_TOKEN` が正しいか確認
2. Discord Developer Portalでボットの権限を確認
3. `TARGET_CHANNEL_ID` が正しいか確認

### APIが接続できない (CORS エラー)
1. バックエンドの `ALLOWED_ORIGINS` 環境変数を確認
2. Vercelのプロダクション URLが正しく設定されているか確認
3. ブラウザの開発者ツールでネットワークエラーを確認
4. バックエンドのログでCORSエラーを確認

### VercelのRoot Directoryに `frontend` が表示されない
1. **"Root Directory"** の右側にある **"Edit"** ボタンをクリック
2. 入力欄に手動で `frontend` と入力
3. **"Continue"** をクリック
4. これで設定が適用されます

### Vercelのビルドが遅い
1. Vercelの無料プランでは並列ビルドに制限があります
2. 通常3〜5分程度かかります
3. エラーがなければ完了を待ちます

---

## 📝 補足情報

### コスト
- **Render Free Plan**: バックエンド無料
  - 制限: 750時間/月、15分間アクセスなしでスリープ（自己Ping機能で対策済み）
- **Vercel Free Plan**: フロントエンド無料
  - 制限: 100GB帯域幅/月、無制限デプロイ
- **UptimeRobot Free Plan**: 50モニターまで無料
- **Supabase Free Plan**: 500MB、無制限API呼び出し

### パフォーマンス最適化
- Renderの有料プラン（$7/月〜）でスリープを無効化
- Vercelの有料プラン（$20/月〜）で帯域幅を拡大
- CDNの利用（Vercelは自動でCDN配信）

### セキュリティ
- 環境変数は絶対にGitにコミットしない
- `.gitignore` に `.env` が含まれていることを確認
- APIキーは定期的にローテーション
- CORS設定は必要最小限のオリジンのみ許可

---

## ✅ デプロイ完了！

お疲れ様でした！これで **AIまう Bot** が本番環境で稼働しています 🎉

- **バックエンド**: Render (常時稼働、自己Ping機能付き)
- **フロントエンド**: Vercel (高速配信、自動デプロイ)

何か問題が発生した場合は、RenderとVercelのログを確認してください。
