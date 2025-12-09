# 🤝 AIまうボット 開発ガイド (Contributing Guide)

## 🌿 ブランチ戦略 (Git Flow Lite)

このプロジェクトでは、以下のシンプルなブランチ運用を採用しています。

### `main` ブランチ (Production)
*   **役割**: 常に「本番環境（Render）」で稼働しているコードと同じ状態です。
*   **変更方法**: `develop` からの Pull Request (PR) マージのみ許可されます。
*   **デプロイ**: このブランチに変更が入ると、Renderへ自動デプロイされます。

### `develop` ブランチ (Development)
*   **役割**: 開発のメインブランチです。最新の機能はここに集まります。
*   **変更方法**:
    *   軽微な修正: 直接コミットOK。
    *   大きな機能: `feature/xxx` ブランチを作成し、そこからPRを送ってください。

## 🛠️ ローカル開発環境 (Dev Mode)

ローカルで開発する際は、本番環境と区別するために **開発モード** で起動してください。
開発モードでは、ボットの返信の末尾に `🛠️ (Dev Check)` というマークが付き、誤爆を防げます。

### 起動方法

```bash
# ワンライナー起動スクリプト (venv有効化 + 環境変数セット)
./run_dev.sh
```

### 環境変数の切り替え (上級者向け)
`.env` ファイルはgit管理外ですが、もし開発専用のトークン（別ボット）を使いたい場合は、
`.env.dev` を作成して読み込ませるなどの改造を推奨します（現在は `run_dev.sh` 内で強制的に `MAU_ENV=development` をセットしています）。

## 📝 コミットメッセージ規約

[Angular Commit Convention](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit) に準拠します。
日本語でOKです。

*   `feat: ...` : 新機能
*   `fix: ...` : バグ修正
*   `docs: ...` : ドキュメント更新
*   `refactor: ...` : リファクタリング
*   `test: ...` : テスト追加
*   `chore: ...` : その他（ビルド設定など）

**例:**
> feat: おみくじ機能を追加
> fix: Geminiのタイムアウトエラーを修正
