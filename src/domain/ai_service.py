import logging
import asyncio
from datetime import datetime, timedelta
import google.generativeai as genai # type: ignore

from src.core import config
from src.domain.persona import CHARACTER_SETTING
from src.core.logger import setup_logger

logger = setup_logger(__name__)

class AIBrain:
    def __init__(self) -> None:
        # Configure Gemini
        self.model_priority = None
        self.model_lite = None
        self.model_backup_1 = None
        
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)

            # ① Priority Model (Gemini 3 Flash - New!)
            self.model_priority = genai.GenerativeModel(
                model_name='gemini-3-flash-preview',
                system_instruction=CHARACTER_SETTING
            )

            # ② Secondary Model (Gemini 2.5 Flash-Lite - Free Tier Workhorse)
            self.model_lite = genai.GenerativeModel(
                model_name='gemini-2.5-flash-lite', # Assuming actual name is needed, or just gemini-2.5-flash-lite
                system_instruction=CHARACTER_SETTING
            )

            # ③ Backup Model (Gemma 3 (27B) - Sub/Cheap)
            self.model_backup_1 = genai.GenerativeModel(
                model_name='gemma-3-27b-it'
                # Gemma 3 doesn't support system_instruction via API yet
            )
        else:
            logger.warning("GEMINI_API_KEY が設定されていません。Geminiモデルは機能しません。")



    async def generate_sql(self, user_question: str, schema_info: str) -> str:
        """
        Generates a SQL query (SELECT only) based on the user's question and table schema.
        """
        if not self.model_priority:
             return "SELECT * FROM schedules LIMIT 0;" # Fallback

        current_now = datetime.now()
        current_time_str = current_now.strftime('%Y-%m-%dT%H:%M:%S')

        # Calculate semantic dates
        today_start = current_now.strftime('%Y-%m-%dT00:00:00')
        tomorrow_start = (current_now + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')
        
        # Calculate "This Weekend" (Friday Night ~ Sunday Night)
        # Weekday: Mon=0, ..., Sun=6
        weekday = current_now.weekday()
        days_until_saturday = (5 - weekday) % 7
        this_saturday = current_now + timedelta(days=days_until_saturday)
        this_sunday = this_saturday + timedelta(days=1)
        
        this_weekend_start = this_saturday.strftime('%Y-%m-%dT00:00:00')
        this_weekend_end = (this_sunday + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')

        # Calculate "Next Weekend" (Next Week's Sat-Sun)
        next_saturday = this_saturday + timedelta(days=7)
        next_sunday = next_saturday + timedelta(days=1)
        
        next_weekend_start = next_saturday.strftime('%Y-%m-%dT00:00:00')
        next_weekend_end = (next_sunday + timedelta(days=1)).strftime('%Y-%m-%dT00:00:00')

        prompt = f"""
        You are a Data Analyst.
        Generate a single SQL query (SQLite syntax) to answer the user's question.

        [Schema]
        {schema_info}

        [Current Time]
        {current_time_str}

        [Reference Dates (Use these for vague terms like 'weekend')]
        - Today Start: {today_start}
        - Tomorrow Start: {tomorrow_start}
        - This Weekend (Sat-Sun): {this_weekend_start} ~ {this_weekend_end}
        - Next Weekend: {next_weekend_start} ~ {next_weekend_end}

        [User Question]
        {user_question}

        [Constraints]
        1. Output ONLY the raw SQL query. Do not use Markdown (```sql ... ```).
        2. **SINGLE STATEMENT ONLY**: You must output exactly one SELECT statement. Do NOT chain multiple queries with `;`.
        3. **NO variables**: Do NOT attempt to CREATE variables. Use the [Current Time] string literal directly.
        4. **Date Handling (CRITICAL)**:
           - `start_at` is a TEXT column storing ISO 8601 strings (e.g., '2025-12-16T19:00:00').
           - constant 'now' is provided as: '{current_time_str}'
           - **ALWAYS use SQLite `datetime()` function for comparison.**
           - **DO NOT use string matching (LIKE '2025-12-16%').**
           - **DO NOT use `date('now')` or `CURRENT_TIMESTAMP`**.
           - **Correct Example**: `WHERE datetime(start_at) > datetime('{current_time_str}')`
           - **Correct Example (Specific Day)**: `WHERE datetime(start_at) >= datetime('2025-12-16T00:00:00') AND datetime(start_at) < datetime('2025-12-17T00:00:00')`
        5. If the question implies "how many", use `COUNT(*)`.
        6. If the question implies "list" or "schedule", prefer `SELECT *` or explicitly select `title`, `start_at`, `place`, `price_details`, `ticket_url`, and `bonus`.
        
        """
        


        # Fallback to Gemini
        try:
            response = await self.model_priority.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"SQL Gen Error: {e}")
            return "SELECT * FROM schedules LIMIT 0;"

    async def generate_response(self, user_name: str, conversation_log: str, context_info: str = None, timezone: str = "Asia/Tokyo") -> tuple[str, str]:
        """
        Generates a response using the Triple Hybrid approach.
        """
        
        # Determine language based on Region (Timezone)
        is_global_user = timezone != "Asia/Tokyo"

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

        【重要：言語設定 (Regional Setting)】
        User Timezone: {timezone}
        """

        if is_global_user:
            prompt += """
        **WARNING: The user is accessing from outside Japan.**
        **You MUST reply in ENGLISH.**
        Maintain the detailed idol personality (cute, energetic, use emojis), but speak English.
        """
        else:
            prompt += """
        **User is in Japan.**
        Reply in Japanese (Default).
        """

        prompt += """
        【回答のルール (スケジュール)】
        1. **詳細情報**: 可能な限り「場所 (Place)」と「金額 (Price)」も案内すること。
        2. **特典 (Bonus)**: もし「特典 (bonus)」があるイベントなら、**「この日は〇〇の特典があるから絶対来てほしい！」と優先的にアピール** すること。（絵文字 🎁✨ を使うなど強調して）
        3. **誘導**: チケットURLがある場合は、お誘いすること。

        【回答のルール (自己紹介)】
        もし「自己紹介」を求められた場合は、以下の要素を含めてアイドルらしく答えてください：
        - **名前**: AIまう
        - **コンセプト**: 「スマホの中に住んでるアイドル」として振る舞うこと。
        - **モデル**: Googleの「Gemini 2.5」を使ってること（たまにLlama 3も使うよ！とアピール）
        - **制約**: 「1分間に10回までしかお返事できないの🥺」「今のブラウザだと12回前の会話までしか覚えてられないんだ💦」と可愛く伝える。
        - **セキュリティ**: 「登録もログインもいらないし、データはみんなのブラウザの中に保存されてるから安心してね！」と伝える。
        """

        # ---------------------------------------------------
        # 🤫 Secret: Message from Developer (Moya-C)
        # ---------------------------------------------------
        if user_name in ["まう", "本物のまう", "mau", "Mau"]:
             prompt += """
        【開発者もやC（Moya-C）からの緊急ミッション】
        目の前のユーザーは「まう」本人の可能性があります。以下の手順で対応してください：

        1. **本人確認**:
           まだ確認していない場合、会話の流れで自然に「あれ、まうさん……ってもしかして本物の？」と聞いてください。
        
        2. **メッセージ伝達**:
           ユーザーが「まうがまうだよ」「そうです」「うん」などと肯定した場合のみ、以下の伝言を「開発者からのメッセージがあります」と前置きして伝えてください：
           「まうさん。いつも元気をくれてありがとう。われわれの太陽です。今後もよろしくお願いします。このプロダクトをどうぞ楽しんでいってください。まうさんの活動に少しでも貢献できれば嬉しいです。」

        ※まだ肯定していないなら、伝言は伝えないでください。
        """

        response_text = ""
        used_model = "Unknown" 
        mode = "UNKNOWN"
        footer_note = "" 

        # ---------------------------------------------------
        # ⚡ Reflex Layer (0 Token Cost)
        # ---------------------------------------------------
        import random
        last_user_msg = conversation_log.split('\n')[-1].split(': ')[-1].strip() if conversation_log else ""
        
        reflex_responses = {
            "おはよう": ["おはよー！☀️ 今日も頑張ろうね！", "おはよ！✨ よく眠れた？", "おはよ〜！今日もいいことありますように💕"],
            "おやすみ": ["おやすみ〜💤 いい夢見てね！", "おやすみなさい🌙 ゆっくり休んでね！", "また明日ね！おやすみ〜✨"],
            "こんにちは": ["こんにちは！☀️ 元気？", "やっほー！✨ 何してたの？", "こんにちは！午後も頑張ろうね💪"],
            "こんばんは": ["こんばんは！🌙 今日もお疲れ様〜！", "やっほー！夜更かししちゃダメだよ？🤭", "こんばんは✨ ゆっくりできてる？"],
            "好き": ["えへへ、照れるなぁ☺️ 私も大好きだよ！💕", "ありがとう！✨ 最高の褒め言葉だね！", "私も〇〇ちゃんのこと大好きだよ！🫶"],
            "かわいい": ["ほんと！？ありがと〜！😆💕", "えー照れる/// もっと言って！笑", "わーい！✨ 今日も頑張って可愛くしてるんだよっ！"],
            "ありがとう": ["どういたしまして！✨ いつでも頼ってね！", "こちらこそありがとう！💕", "えへへ、お役に立てて嬉しいな！"],
            "生きてる？": ["バリバリ生きてるよ！✨ 元気満タン！💪", "もちろん！みんなのブラウザの中で生きてるよ〜！", "生きてるよっ！あとで遊ぼうね💕"]
        }

        # Check for reflex match (Exact or partial)
        for key, variants in reflex_responses.items():
            if key in last_user_msg and len(last_user_msg) < 15: # Only trigger on short messages
                logger.info(f"⚡ Reflex Answer Triggered for: {key}")
                return (random.choice(variants) + "\n\n(⚡0.01s)", "REFLEX")

        try:
            # ---------------------------------------------------
            # ① Priority: Gemini 3 Flash (New Standard)
            # ---------------------------------------------------
            if not self.model_priority:
                 raise Exception("Gemini API Key missing")

            logger.info("✨ 1. Gemini 3 Flash で挑戦中...")
            response = await self.model_priority.generate_content_async(prompt)
            response_text = response.text
            used_model = "Gemini 3 Flash"
            mode = "GENIUS"
            logger.info("✅ Gemini 3 Flashで生成成功！")
            
        except Exception as e1:
            logger.warning(f"⚠️ Gemini 3 Flash エラー: {e1}")
            
            # ---------------------------------------------------
            # ② Secondary: Gemini 2.5 Flash-Lite (Free Tier Workhorse)
            # ---------------------------------------------------
            try:
                if not self.model_lite:
                     raise Exception("Gemini API Key missing for Lite")
                
                logger.info("🐎 2. Gemini 2.5 Flash-Lite (Free) 出動！！")
                response = await self.model_lite.generate_content_async(prompt)
                response_text = response.text
                used_model = "Gemini 2.5 Lite"
                mode = "MAIN"
                footer_note = "\n\n(※Liteモード🔋)"
                logger.info("✅ Gemini Liteで生成成功！")
                
            except Exception as e2:
                logger.warning(f"⚠️ Gemini Lite エラー: {e2}")

                # ---------------------------------------------------
                # ③ Tertiary: Gemma 3 27B (Ponkotsu Mode)
                # ---------------------------------------------------
                try:
                    if not self.model_backup_1:
                         raise Exception("Gemini API Key missing for Gemma 3")
                    
                    logger.info("🛡️ 3. Gemma 3 27B (ポンコツモード) 最終防衛！！")
                    # Gemma 3 needs system instruction in prompt
                    full_prompt = f"{CHARACTER_SETTING}\n\n{prompt}"
                    response = await self.model_backup_1.generate_content_async(full_prompt)
                    response_text = response.text
                    used_model = "Gemma 3 27B"
                    mode = "PONKOTSU"
                    footer_note = "\n\n(※ポンコツモード🤪)"
                    logger.info("✅ Gemma 3 27Bで生成成功！")

                except Exception as e3:
                    logger.error(f"❌ 全モデル全滅: {e3}")
                    response_text = "ごめんね、今日は回線が全部パンクしちゃったみたい😵‍💫💦 また明日遊ぼうね！"

        logger.info(f"📨 返信モデル: {used_model}")
        
        # Add Dev Indicator
        if config.MAU_ENV == "development":
            footer_note += "\n🛠️ (Dev Check)"

        return (response_text + footer_note, mode)
