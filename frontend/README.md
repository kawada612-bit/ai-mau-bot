# 🩵 AIまう フロントエンド

Next.js 16 (App Router) を使用した、AIまうとチャットできるWebアプリケーションです。

## ✨ 主な機能

### 💬 リアルタイムチャット
- **疑似ストリーミング表示**: AIの応答を1文字ずつアニメーション表示
- **タイピングインジケーター**: AI思考中の視覚的フィードバック
- **自動スクロール**: 新しいメッセージに自動追従

### 💾 永続化機能
- **会話履歴の保存**: LocalStorageを使用してページリロード後も会話を保持
- **ユーザー名のカスタマイズ**: 名前を設定・変更可能（自動保存）
- **長期コンテキスト**: 最大12件の会話履歴をAPIに送信

### 🎨 リッチUI
- **モダンデザイン**: グラスモーフィズム、グラデーション、アニメーション
- **レスポンシブ**: モバイル・デスクトップ対応
- **OGPリンクカード**: URLを含むメッセージでリッチカードを自動表示
  - OGPメタデータ（タイトル、説明、画像）を自動取得
  - 取得失敗時はシンプルなカードにフォールバック
- **クリック可能なURL**: チャット内のURLをクリックして新しいタブで開ける

## 🛠️ 技術スタック

- **フレームワーク**: Next.js 16 (App Router, Turbopack)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS + Custom CSS
- **アニメーション**: Framer Motion
- **アイコン**: Lucide React
- **状態管理**: React Hooks + Custom Hooks

## 🚀 セットアップ

### 環境変数の設定

`.env.local` ファイルを作成し、以下を設定してください：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

本番環境では、バックエンドAPIのURLを設定してください。

### インストール & 起動

```bash
# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev

# ブラウザで http://localhost:3000 を開く
```

### ビルド

```bash
# 本番ビルド
npm run build

# 本番サーバー起動
npm start
```

## 📁 ディレクトリ構成

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # メインチャットページ
│   │   ├── layout.tsx         # ルートレイアウト
│   │   └── globals.css        # グローバルスタイル
│   ├── components/            # Reactコンポーネント
│   │   └── link-card.tsx      # OGPリンクカード
│   ├── hooks/                 # カスタムフック
│   │   └── use-local-storage.ts  # LocalStorage永続化フック
│   └── lib/                   # ユーティリティ
│       └── utils.ts           # ヘルパー関数
├── public/                    # 静的ファイル
└── package.json              # 依存関係
```

## 🎨 主要コンポーネント

### `page.tsx`
メインのチャットインターフェース。以下の機能を含みます：
- メッセージ送受信
- 会話履歴管理
- ユーザー名管理
- URL検出とリンクカード表示
- URLのリンク化（クリック可能）

### `link-card.tsx`
OGP（Open Graph Protocol）を使用したリッチリンクカード：
- バックエンドAPIからOGPメタデータを取得
- 画像、タイトル、説明を表示
- ローディング状態とエラーハンドリング
- **グレースフルデグラデーション**: OGP取得失敗時はシンプルなカードを表示

### `use-local-storage.ts`
LocalStorageと同期する状態管理フック：
- SSR対応（Hydration Mismatch回避）
- 型安全な状態管理
- 自動シリアライズ/デシリアライズ

## 🔌 API連携

### `/api/chat` (POST)
チャットメッセージを送信し、AIの応答を取得します。

**リクエスト:**
```json
{
  "text": "こんにちは",
  "user_name": "ユーザー名",
  "history": [
    { "role": "user", "text": "前のメッセージ" },
    { "role": "ai", "text": "前の応答" }
  ]
}
```

**レスポンス:**
```json
{
  "response": "やほす〜！元気してた？✨"
}
```

### `/api/ogp` (POST)
URLからOGPメタデータを取得します。

**リクエスト:**
```json
{
  "url": "https://example.com"
}
```

**レスポンス:**
```json
{
  "title": "ページタイトル",
  "description": "ページの説明",
  "image": "https://example.com/image.jpg"
}
```

## 🎨 デザインシステム

### カラーパレット
- **プライマリ**: Cyan (400-500)
- **アクセント**: Blue (400-500)
- **背景**: Sky (50-100)
- **テキスト**: Slate (600-800)

### アニメーション
- **メッセージ出現**: Spring animation (Framer Motion)
- **タイピング**: Bounce animation
- **ホバー**: Scale & Color transitions

## 📝 開発ガイド

### カスタムフックの追加
`src/hooks/` ディレクトリに新しいフックを追加できます。

### コンポーネントの追加
`src/components/` ディレクトリに新しいコンポーネントを追加できます。

### スタイルのカスタマイズ
`src/app/globals.css` でグローバルスタイルとカスタムCSSクラスを定義できます。

## 🚀 デプロイ

### Vercel (推奨)
```bash
# Vercel CLIでデプロイ
npm i -g vercel
vercel
```

### その他のプラットフォーム
Next.js 16はNode.js 18.18以降が必要です。
環境変数 `NEXT_PUBLIC_API_URL` を本番APIのURLに設定してください。

## 📚 参考リンク

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [Lucide Icons](https://lucide.dev/)
