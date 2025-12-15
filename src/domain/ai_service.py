import logging
import asyncio
from datetime import datetime
import google.generativeai as genai # type: ignore
from groq import Groq
from src.core import config
from src.domain.persona import CHARACTER_SETTING
from src.core.logger import setup_logger

logger = setup_logger(__name__)

class AIBrain:
    def __init__(self) -> None:
        # Configure Gemini
        self.model_priority = None
        self.model_backup_1 = None
        
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)

            # ① Priority Model (Gemini 2.5 Flash)
            self.model_priority = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=CHARACTER_SETTING
            )

            # ② Backup Model (Gemini 2.5 Flash Lite)
            self.model_backup_1 = genai.GenerativeModel(
                model_name='gemini-2.5-flash-lite',
                system_instruction=CHARACTER_SETTING
            )
        else:
            logger.warning("GEMINI_API_KEY が設定されていません。Geminiモデルは機能しません。")

        # Configure Groq
        # ③ Final Weapon (Groq - Llama 3)
        self.groq_client: Groq | None = None
        if config.GROQ_API_KEY:
            self.groq_client = Groq(api_key=config.GROQ_API_KEY)
            logger.info("✅ Groqクライアント(Llama 3)の準備完了")
        else:
            logger.warning("GROQ_API_KEY未設定: Llama 3 バックアップは無効です")

    async def generate_sql(self, user_question: str, schema_info: str) -> str:
        """
        Generates a SQL query (SELECT only) based on the user's question and table schema.
        """
        if not self.model_priority:
             return "SELECT * FROM schedules LIMIT 0;" # Fallback

        current_time_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        prompt = f"""
        You are a Data Analyst.
        Generate a single SQL query (SQLite syntax) to answer the user's question.

        [Schema]
        {schema_info}

        [Current Time]
        {current_time_str} (Use this as 'now' for relative dates)

        [User Question]
        {user_question}

        [Constraints]
        1. Output ONLY the raw SQL query. Do not use Markdown (```sql ... ```).
        2. **SINGLE STATEMENT ONLY**: You must output exactly one SELECT statement. Do NOT chain multiple queries with `;`.
        3. **NO variables**: Do NOT attempt to CREATE variables or `SELECT ... AS current_time`. Use the [Current Time] string literal directly in your WHERE clause comparisons.
        4. **Date Handling Requirments**:
           - `start_at` is a TEXT column (ISO 8601).
           - Do NOT use SQLite's `date('now')` or `CURRENT_DATE`.
           - Compare `start_at` directly with calculated strings based on [Current Time].
           - Example for "Tomorrow": If Current Time is '2025-10-10...', query `start_at LIKE '2025-10-11%'`.
        5. If the question implies "how many", use `COUNT(*)`.
        6. If the question implies "list" or "schedule", prefer `SELECT *` or explicitly select `title`, `start_at`, `place`, `price_details`, `ticket_url`, and `bonus`.
        
        """
        
        # Try Groq (Llama 3) first
        if self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a SQL expert. Output ONLY the raw SQL query string. No Markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=256
                )
                sql = completion.choices[0].message.content.strip()
                return sql.replace("```sql", "").replace("```", "").strip()
            except Exception as e:
                logger.warning(f"⚠️ Groq SQL Gen failed: {e}. Falling back to Gemini.")

        # Fallback to Gemini
        try:
            response = await self.model_priority.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"SQL Gen Error: {e}")
            return "SELECT * FROM schedules LIMIT 0;"

    async def generate_response(self, user_name: str, conversation_log: str, context_info: str = None) -> str:
        """
        Generates a response using the Triple Hybrid approach.
        """
        
        prompt = f"""
        あなたはアイドルの「AIまう」です。
        現在、ファンの「{user_name}」さんからメッセージが届きました。

        【会話履歴】
        {conversation_log}
        """

        if context_info:
            prompt += f"""
        【参考データ (分析結果)】
        以下はユーザーの質問に関連するデータベース検索結果です。
        このデータに基づいて回答してください。データがない場合は「予定はないみたい」と答えてください。
        ------------------------
        {context_info}
        ------------------------
            """

        prompt += f"""
        【指示】
        1. mau_profile.txt の設定（キャラ設定）を守ってください。
        2. 文頭で必ず「{user_name}！」や「{user_name}ちゃん！」と名前を呼んでください。
        3. **相手が英語で話しかけてきた場合は英語で、日本語なら日本語で返信してください。**
           (If the user speaks English, reply in English with the same idol personality.)
        4. 親しい友達のようにタメ口で返信してください。
        5. **返信は基本「200文字以内」で短く返してください。ただし、ライブの告知やスケジュール詳細を伝える場合は、情報が漏れないように文字数制限を無視して長くなっても構いません。**

        【回答のルール (スケジュール)】
        1. **詳細情報**: 可能な限り「場所 (Place)」と「金額 (Price)」も案内すること。
        2. **特典 (Bonus)**: もし「特典 (bonus)」があるイベントなら、**「この日は〇〇の特典があるから絶対来てほしい！」と優先的にアピール** すること。（絵文字 🎁✨ を使うなど強調して）
        3. **誘導**: チケットURLがある場合は、お誘いすること。

        【回答のルール (自己紹介)】
        もし「自己紹介」を求められた場合は、以下の要素を含めてアイドルらしく答えてください：
        - **名前**: AIまう
        - **モデル**: Googleの「Gemini 2.5」を使ってること（たまにLlama 3も使うよ！とアピール）
        - **機能**: おしゃべりと、最新のライブスケジュールの共有ができること。
        - **制約**: 「1分間に10回までしかお返事できないの🥺」「今のブラウザだと6回前の会話までしか覚えてられないんだ💦」と可愛く伝える。
        - **セキュリティ**: 「データはみんなのブラウザの中に保存されてるから安心してね！」と伝える。
        """

        response_text = ""
        used_model = "Groq Llama 3" # For logging
        footer_note = "" # Annotation for user

        try:
            # ---------------------------------------------------
            # ① Groq Llama 3 (Main - Priority)
            # ---------------------------------------------------
            if not self.groq_client:
                raise Exception("Groq API Key missing")

            logger.info(f"🔥 1. Groq (Llama 3) で挑戦中...")
            # Call Groq API
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile", # High performance model
                messages=[
                    # Inject system setting
                    {"role": "system", "content": CHARACTER_SETTING},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            response_text = completion.choices[0].message.content or ""
            logger.info("✅ Groqで生成成功！")
        
        except Exception as e1:
            logger.warning(f"⚠️ Groq Llama 3 エラー: {e1}")
            try:
                # ---------------------------------------------------
                # ② Gemini 2.5 Flash (Backup 1)
                # ---------------------------------------------------
                if not self.model_priority:
                     raise Exception("Gemini API Key missing")

                logger.info("✨ 2. Gemini 2.5 Flash に切り替えます...")
                response = await self.model_priority.generate_content_async(prompt)
                response_text = response.text
                used_model = "Gemini 2.5"
                footer_note = "\n\n(※バックアップモード🔄)"
                
            except Exception as e2:
                logger.warning(f"⚠️ Gemini 2.5 エラー: {e2}")
                # ---------------------------------------------------
                # ③ Gemini 2.5 Flash Lite (Backup 2)
                # ---------------------------------------------------
                if self.model_backup_1:
                    logger.info("♻️ 3. Gemini 2.5 Lite 出動！！")
                    try:
                        response = await self.model_backup_1.generate_content_async(prompt)
                        response_text = response.text
                        used_model = "Gemini Lite"
                        footer_note = "\n\n(※省エネモード🔋)"
                        logger.info("✅ Gemini Liteで生成成功！")
                        
                    except Exception as e3:
                        logger.error(f"❌ Gemini Liteもエラー: {e3}")
                        response_text = "ごめんね、今日は回線が全部パンクしちゃったみたい😵‍💫💦 また明日遊ぼうね！"
                else:
                    response_text = "ごめんね、ちょっと調子悪いみたい…💦 (Geminiキー未設定)"

        logger.info(f"📨 返信モデル: {used_model}")
        
        # Add Dev Indicator
        if config.MAU_ENV == "development":
            footer_note += "\n🛠️ (Dev Check)"

        return response_text + footer_note
