# 📋 AIまうちゃん 機能バックログ

**最終更新:** v2.1 (Phase 5 Completed)

## 🚨 緊急対応 (Hot Fix)
**ボットの生存に関わる最優先タスク。**

- [x] **HOT-01: 常時起動化 (UptimeRobot)** `実装済`
  - Renderの無料サーバーが15分で寝てしまうのを防ぐ。
- [x] **HOT-02: トリプルハイブリッド (Groq)** `実装済`
  - Geminiのリミット切れ対策。Groq (Llama 3) ロジック組み込み済み。

---

## 🏗️ アーキテクチャ刷新 (Architecture & Infra)
**拡張性と保守性を高めるための構造改革タスク。【最優先】**

- [x] **ARCH-01: マイクロサービス構成への分離 (Epic)** `実装済`
  - リポジトリを3つに分割する (`ai-mau-core`, `ai-mau-web`, `mau-scheduler`) 代わりに、モジュラモノリス構成 (`src/app`, `src/domain`, `src/workers`) へ移行完了。
- [x] **INFRA-01: Supabaseデータベース構築** `実装済`
  - スケジュール管理用のDB作成。テーブル `schedules` の定義とAPIキー取得。
- [x] **WORKER-01: TimeTree同期クローラー (mau-scheduler)** `実装済`
  - `src/workers/scheduler.py` 実装済み。AI補正とDry Runモード搭載。

---

## 🛡️ セキュリティ & コアロジック (Security & Core)
**ボットの頭脳と安全性を強化するタスク。**

- [ ] **CORE-01: マルチプロフィール対応 (メンバー切り替え)** `高`
  - `data/profiles/` 構成への変更。「まう」「まな」「くるみ」等の人格切り替えロジック実装。
- [ ] **CORE-02: 「全員(All)」モード実装** `高`
  - メンバー同士がわちゃわちゃ話す「楽屋トーク」プロファイルの作成 (`all.txt`)。
- [x] **SEC-01: テスト環境構築** `実装済`
  - Dev用ボット運用フローの確立。
- [ ] **SEC-02: API認証 (Secret Key)** `高`
  - `ai-mau-core` のAPIにヘッダー認証(`MAU_API_SECRET`)を導入。
- [ ] **SEC-03: 管理者IDの秘匿** `中`
  - ソースコード内のIDを環境変数化。
- [ ] **SEC-04: APIエンドポイント実装** `高`
  - Flaskを拡張し、外部(Web/LINE)から会話できる `/api/chat` を作成。
- [x] **SEC-05: 安全性強化 (Safety Guard)** `実装済`
  - スケジューラーのDry Runモード、AIハルシネーション対策（日付バリデーション）、Graceful Shutdown対応。

---

## 🚀 機能追加 (Features & Web)
**ユーザー体験を向上させる新機能。**

- [ ] **WEB-01: Webアプリ化 (ai-mau-web)** `中` (旧IDEA-01)
  - Next.js/Vue.js でチャット画面とスケジュール一覧を作成。Vercelデプロイ。
- [ ] **FEAT-01: 管理者アナウンス** `中`
  - `!announce` コマンド実装。
- [ ] **FEAT-02: 定期実行タスク** `中`
  - 挨拶やライブ煽りの自動投稿。
- [x] **FEAT-03: 高IQスケジュール分析 (High-IQ Analytics)** `実装済`
  - ユーザーの質問（「今月のライブ数は？」「次の予定は？」）に対して、インメモリSQLiteとAI生成SQLを用いて回答する機能を実装。

---

## 🛠️ 開発環境 (Dev Env)
**開発効率とコード品質を高めるタスク。**

- [x] **DEV-01: Windows環境対応** `実装済`
  - `run_dev.bat` の作成と文字コード対応。
- [x] **DEV-02: コード品質向上** `実装済`
  - ロギング基盤 (`src.core.logger`)、型ヒント導入。

---

## 📂 検討中・調査 (Backlog)
**将来的な拡張アイデア。**

- [ ] **IDEA-02: LINE Bot 対応** `中`
  - コアAPI (`ai-mau-core`) を利用してLINEでも会話可能にする。
- [ ] **IDEA-03: X (旧Tw) 情報取得** `低`
- [ ] **IDEA-04: X (旧Tw) 自動投稿** `低`
- [ ] **IDEA-05: 長期記憶 (Supabase)** `低`
  - ユーザーごとの会話履歴をDBに保存。
- [ ] **IDEA-06: 画像生成** `低`
- [ ] **IDEA-07: おみくじ・占い** `低`

---

## ✅ 実装済み (Done)
- [x] 基本会話機能
- [x] キャラクター人格 (Wiki準拠)
- [x] トリプルハイブリッド (Gemini ⇔ Groq)
- [x] 制限・エラー対応
- [x] 長文自動分割
- [x] システム通知無視
- [x] バイリンガル対応