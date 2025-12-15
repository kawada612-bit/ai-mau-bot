# **📱 AI Mau Web App Requirements (Service Focused)**

**「最高のチャット体験」** を最優先事項とした、AIまうWebアプリのサービス要件定義書。

## **1\. プロジェクト・コンセプト**

* **Core Value**: 「スマホの中に、本物のアイドルがいる」。  
* **Experience**: ストレスゼロ。Apple純正アプリのような滑らかさと、リアルな会話のテンポ感を提供する。  
* **Phase**: MVP (Minimum Viable Product) 実装完了。AIチャット、PWA、ユーザー名設定などの基本機能を実装済み。

## **2\. サービス要件 (Service Requirements)**

### **2.1 💬 Ultimate AI Chat (チャット体験)**

Discord版の移植ではなく、**スマホネイティブアプリのようなリッチな体験** をWebで実現する。

* **ログイン不要 (No Login)**  
  * アプリを開いた瞬間に会話が始まる（Onboardingゼロ）。  
*   **ログイン不要 (No Login)**
    *   アプリを開いた瞬間に会話が始まる（Onboardingゼロ）。
    *   **セッション管理**: ブラウザの UUID (LocalStorage) でユーザーを識別し、会話履歴を保持する。
    *   **会話履歴の送信**: 直近12件のメッセージをバックエンドAPIに送信し、AIが文脈を理解できるようにする。
    *   **データの永続性**: ブラウザを閉じても会話が消えない（LocalStorage）。全履歴はクライアント側に保存され、サーバーには送信されない。
*   **ストレスフリー・アニメーション (Motion UX)**
    *   **Framer Motion** を使用し、以下の「待機時間を感じさせない」演出を行う。
        1.  **Typing Indicator**: AIが考え中・入力中であることを示す「...」のアニメーション（Apple iMessage風）。
        2.  **Streaming Response**: AIの回答を一括表示するのではなく、**1文字ずつ** パラパラと表示し、人間が打っているようなリズムを作る。
        3.  **Message Bubble**: メッセージ送信時、下からふわっと湧き上がるようなバネのあるアニメーション (Spring Animation)。
*   **PWA対応 (Implemented)**
    *   マニフェストファイル (`manifest.json`) の生成。
    *   ホーム画面への追加、オフライン対応（Service Worker）。
    *   スプラッシュスクリーン、アイコンの設定。
*   **マルチペルソナ拡張性 (Future Proofing)**
    *   UI上に「メンバー切り替え」のスペース（アイコン等）を予め確保しておく（MVPでは「まう」のみ活性化）。
    *   APIリクエスト時に character\_id: "mau" を送信する設計にし、将来的に「まな」「くるみ」などを容易に追加できるようにする。

### **2.2 🎨 UIデザイン (Apple Human Interface Guidelines)**

最新の iOS (iOS 17/18) のデザイン哲学を取り入れる。

*   **Typography**:
    *   System Font (\-apple-system, San Francisco) を使用。
    *   大きめの見出し、太めのウェイトで階層を明確にする。
*   **Glassmorphism & Depth**:
    *   すりガラス効果 (backdrop-filter: blur) をヘッダーや入力欄に使用し、コンテンツの奥行きを表現する。
    *   べた塗りではなく、微細なグラデーションとシャドウで「触れそうな」質感を出す。
*   **Layout**:
    *   **Bottom Navigation / Input**: 親指の届く範囲に操作系を集中させる。
    *   **Dark Mode**: OS設定に自動追従する完全なダークモード対応。
*   **Feedback**:
    *   ボタン押下時に微細な縮小アニメーションを入れる（Haptic Touchの視覚的代用）。

### **2.3 🛡️ セキュリティ & 安全性 (Maximum Security)**

ログインなしの公開サービスであることを前提に、以下の対策を徹底する。

*   **API Abuse Prevention (悪用防止)**:
    *   **Rate Limiting**: IPアドレスごとに「1分間に〇回まで」の制限を厳しくかける（DDoS/コスト爆発防止）。
    *   **ReCAPTCHA v3**: ユーザー操作を阻害しない形（Invisible）でBot対策を行う。
*   **Content Safety (入力・出力ガード)**:
    *   **Input Validation**: 極端な長文やスクリプトタグなどをフロントエンド/バックエンド両方で弾く。
    *   **Prompt Injection対策**: AIに対して「あなたはAIではありません」等の命令書き換えを無効化するガードレール層を挟む。

## **3\. システム要件概要 (System Constraints)**

### **Frontend (Next.js)**

*   **Framework**: Next.js 16 (App Router)

*   **Styling**: Tailwind CSS \+ clsx / tailwind-merge
*   **Animation**: framer-motion (必須)
*   **Icons**: lucide-react (AppleのSF Symbolsに近いシンプルな線画アイコン)

### **Backend (FastAPI)**

*   **Framework**: FastAPI (Python)
*   **Architecture**:
    *   Discord BotとWeb APIを同一プロセス（または並行プロセス）で稼働させ、メモリ（DBキャッシュ等）を共有することで高速化を図る。
    *   POST /api/chat: ストリーミングレスポンス (StreamingResponse) をサポートする。

## **4\. 開発ロードマップ (Revised)**

1.  **Step 1: Backend Upgrade**
    *   既存の server.py (Flask) を **FastAPI** に置き換え、Discord Botと共存させる。
    *   ストリーミング対応の /api/chat エンドポイントを作成。
2.  **Step 2: Frontend Foundation**
    *   Next.js プロジェクト作成。AppleライクなUIコンポーネントの実装。
3.  **Step 3: Core Chat Logic (Done)**
    *   ストリーミング受信処理、アニメーション実装。
    *   **ユーザー名設定**, **PWA対応** の実装。
4.  **Step 4: Security Hardening (Done)**
    *   レート制限、バリデーションの実装。
    *   Google Analytics 4 (GA4) の導入。