# 📋 非機能要件 (Non-Functional Requirements)

このドキュメントは、AIまうプロジェクトの非機能要件を定義します。

## 1. パフォーマンス要件

### 1.1 応答時間
| コンポーネント  | 要件                                  | 現状                             |
| :-------------- | :------------------------------------ | :------------------------------- |
| **Discord Bot** | メッセージ受信から応答開始まで3秒以内 | タイピングインジケーター即座表示 |
| **Web API**     | `/api/chat` エンドポイント30秒以内    | タイムアウト設定済み             |
| **OGP取得**     | `/api/ogp` エンドポイント10秒以内     | httpxタイムアウト10秒            |
| **データ分析**  | SQL生成・実行5秒以内                  | インメモリSQLite使用             |

### 1.2 スループット
- **同時接続**: Discord Bot: 複数チャンネル対応、Web API: FastAPI非同期処理
- **データキャッシュ**: Analytics Service 5分間キャッシュ（Supabaseクエリ削減）
- **メッセージ処理**: Discord 2000文字制限対応（自動分割）

### 1.3 リソース使用量
- **メモリ**: インメモリSQLite使用（スケジュールデータ全件展開）
- **API制限**: 
  - Gemini API: 無料枠内で運用
  - Groq API: フォールバック用
  - Supabase: 5分キャッシュで負荷軽減

## 2. 可用性・信頼性要件

### 2.1 稼働率
- **目標稼働率**: 99%以上
- **監視**: UptimeRobot による24時間監視
- **ホスティング**: Render Free Plan（スリープ対策済み）

### 2.2 フォールバック機構
```
Gemini 2.5 Flash (Main)
  ↓ エラー時
Gemini 2.5 Flash Lite (Sub)
  ↓ エラー時
Groq Llama 3.3 (Fallback)
```

### 2.3 エラーハンドリング
- **AI応答タイムアウト**: 30秒（Discord Bot、Web API共通）
- **SQL実行エラー**: SELECT以外のクエリをブロック
- **OGP取得失敗**: シンプルなリンクカードにフォールバック
- **ログ記録**: すべてのエラーをロギング

### 2.4 データ整合性
- **データ同期**: TimeTree → Groq AI解析 → Supabase（定期実行）
- **トランザクション**: Supabase PostgreSQL ACID準拠
- **バックアップ**: Supabase自動バックアップ

## 3. セキュリティ要件

### 3.1 認証・認可
- **Discord Bot**: Discord Token認証
- **Web API**: CORS設定（現状: `allow_origins=["*"]`）
  - ⚠️ **推奨**: 本番環境では特定オリジンのみ許可
- **環境変数**: `.env` ファイルで機密情報管理（Git除外）

### 3.2 データ保護
- **通信**: HTTPS/WSS（Discord、Supabase、AI API）
- **API Key**: 環境変数で管理、コードに直接記載しない
- **ユーザーデータ**: 
  - Discord: ユーザー名のみ使用
  - Web: LocalStorageに会話履歴保存（クライアント側）

### 3.3 入力検証
- **SQL Injection対策**: 
  - SELECT以外のクエリをブロック
  - Pandas `read_sql_query` 使用（パラメータ化）
- **XSS対策**: React自動エスケープ
- **API入力**: Pydantic バリデーション

### 3.4 脆弱性管理
- **依存関係**: 定期的な `pip` / `npm` パッケージ更新
- **セキュリティスキャン**: GitHub Dependabot（推奨）

## 4. スケーラビリティ要件

### 4.1 水平スケーリング
- **現状**: モノリシック構成（単一Renderインスタンス）
- **将来**: FastAPI + Discord Botの分離デプロイ可能

### 4.2 データベーススケーリング
- **Supabase**: PostgreSQL（Free Plan: 500MB）
- **拡張性**: 必要に応じて有料プランへ移行可能

### 4.3 キャッシュ戦略
- **Analytics Service**: 5分間メモリキャッシュ
- **Frontend**: LocalStorage永続化（会話履歴、ユーザー名）

## 5. 保守性・運用性要件

### 5.1 ログ・監視
- **ロギング**: Python `logging` モジュール使用
- **ログレベル**: INFO（通常）、ERROR（エラー）
- **監視**: UptimeRobot（死活監視）

### 5.2 デプロイ
- **CI/CD**: Git Push → Render自動デプロイ
- **ブランチ戦略**: Git Flow Lite（`main` / `develop`）
- **環境**: 本番環境のみ（Render Free Plan）

### 5.3 コード品質
- **型チェック**: TypeScript（Frontend）、Type Hints（Backend）
- **コードスタイル**: 
  - Python: PEP 8準拠
  - TypeScript: ESLint + Prettier（推奨）
- **テスト**: pytest（Backend）、手動テスト（Frontend）

### 5.4 ドキュメント
- **README.md**: プロジェクト概要、セットアップ手順
- **SPEC.md**: 技術仕様、アーキテクチャ
- **CONTRIBUTING.md**: 開発ガイド
- **NFR.md**: 非機能要件（本ドキュメント）

## 6. ユーザビリティ要件

### 6.1 Discord Bot
- **応答性**: タイピングインジケーター表示
- **文字数制限**: 200文字以内（原則）、詳細情報は例外
- **空気を読む**: メンション判定、他人への割り込み防止

### 6.2 Web チャット
- **レスポンシブ**: モバイル・デスクトップ対応
- **アニメーション**: Framer Motion（滑らかな表示）
- **疑似ストリーミング**: 1文字ずつ表示（体感速度向上）
- **永続化**: ページリロード後も会話保持

### 6.3 アクセシビリティ
- **セマンティックHTML**: 適切なタグ使用
- **キーボード操作**: Enter送信、Shift+Enter改行
- **カラーコントラスト**: WCAG AA準拠（推奨）

## 7. 互換性要件

### 7.1 ブラウザ対応
- **対象**: Chrome、Firefox、Safari、Edge（最新版）
- **JavaScript**: ES2020+
- **CSS**: Flexbox、Grid、CSS Variables

### 7.2 プラットフォーム
- **Backend**: Python 3.10+
- **Frontend**: Node.js 18.18+
- **OS**: Windows、macOS、Linux

### 7.3 外部サービス
- **Discord API**: discord.py 2.x
- **Gemini API**: google-generativeai 0.8.3+
- **Groq API**: groq SDK
- **Supabase**: supabase-py

## 8. コンプライアンス要件

### 8.1 ライセンス
- **プロジェクト**: MIT License
- **依存関係**: オープンソースライセンス準拠

### 8.2 データプライバシー
- **個人情報**: ユーザー名のみ収集（Discord表示名）
- **会話ログ**: 
  - Discord: 直近10件のみメモリ保持
  - Web: クライアント側LocalStorageのみ
- **データ保持期間**: 永続保存なし（セッションベース）

### 8.3 利用規約
- **Discord Bot**: Discord Terms of Service準拠
- **AI API**: 各プロバイダーの利用規約準拠
  - Google AI Studio
  - Groq Cloud

## 9. 制約事項

### 9.1 技術的制約
- **Free Plan制限**:
  - Render: スリープあり（UptimeRobotで対策）
  - Supabase: 500MB、帯域幅制限
  - Gemini API: 無料枠RPM制限
  - Groq API: 無料枠RPM制限

### 9.2 機能的制約
- **Discord**: 2000文字メッセージ制限
- **OGP**: 外部サイトのメタデータ依存
- **Analytics**: Supabaseデータのみ分析可能

### 9.3 運用制約
- **単一インスタンス**: 現状スケールアウト未対応
- **手動デプロイ**: Git Push後のRender自動デプロイのみ

## 10. 将来の改善項目

### 10.1 パフォーマンス
- [ ] Redis導入（分散キャッシュ）
- [ ] CDN導入（Frontend静的ファイル）
- [ ] データベースインデックス最適化

### 10.2 セキュリティ
- [ ] CORS設定の厳格化
- [ ] Rate Limiting実装
- [ ] JWT認証（Web API）

### 10.3 可用性
- [ ] マルチリージョンデプロイ
- [ ] データベースレプリケーション
- [ ] 自動フェイルオーバー

### 10.4 機能
- [ ] ユーザー認証（Web）
- [ ] 会話履歴のサーバー保存
- [ ] リアルタイムストリーミング応答
- [ ] 音声入力対応

---

**最終更新**: 2025-12-13  
**バージョン**: 1.0.0
