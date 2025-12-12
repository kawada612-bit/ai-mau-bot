## **4\. 開発ロードマップ (Revised)**

1. **Step 1: Backend Upgrade** ✅  
   * 既存の server.py (Flask) を **FastAPI** に置き換え、Discord Botと共存させる。  
   * ストリーミング対応の /api/chat エンドポイントを作成。  
2. **Step 2: Frontend Foundation** ✅  
   * Next.js プロジェクト作成。AppleライクなUIコンポーネントの実装。  
3. **Step 3: Core Chat Logic** ✅  
   * ストリーミング受信処理、アニメーション実装。  
4. **Step 4: Security Hardening** ✅ **[Phase 14 完了]**  
   * **レート制限**: slowapiを使用し、10リクエスト/分の制限を実装。
   * **入力バリデーション**: Pydantic Fieldで500文字制限、ユーザー名50文字制限を実装。
   * **CORS制限**: 環境変数ALLOWED_ORIGINSで許可オリジンを設定可能に。
   * **プロンプトインジェクション対策**: AIペルソナにセキュリティガードレールを追加。

---

## **5\. Phase 14 実装詳細**

### セキュリティ機能一覧

| 機能                           | 実装場所                                  | 詳細                                           |
| ------------------------------ | ----------------------------------------- | ---------------------------------------------- |
| レート制限                     | `src/app/server.py`                       | slowapi使用、10リクエスト/分（IP単位）         |
| 入力バリデーション             | `src/app/server.py`                       | Pydantic Field: text 500文字、user_name 50文字 |
| CORS制限                       | `src/core/config.py`, `src/app/server.py` | 環境変数`ALLOWED_ORIGINS`で設定                |
| プロンプトインジェクション対策 | `src/domain/persona.py`                   | セキュリティガードレールをペルソナに追加       |

### テスト方法

セキュリティテストスクリプト: `test_security.py`

```bash
# サーバー起動
uvicorn src.app.server:app --reload

# 別ターミナルでテスト実行
python test_security.py
```
