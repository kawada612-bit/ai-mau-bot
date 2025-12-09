
import google.generativeai as genai
from groq import Groq
from src import config
from src.ai.persona import CHARACTER_SETTING

# Configure Gemini
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)

    # ① Priority Model (Gemini 2.5 Flash)
    model_priority = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=CHARACTER_SETTING
    )

    # ② Backup Model (Gemini 2.5 Flash Lite)
    model_backup_1 = genai.GenerativeModel(
        model_name='gemini-2.5-flash-lite',
        system_instruction=CHARACTER_SETTING
    )
else:
    print("⚠️ GEMINI_API_KEY が設定されていません。Geminiモデルは機能しません。")
    model_priority = None
    model_backup_1 = None

# Configure Groq
# ③ Final Weapon (Groq - Llama 3)
if config.GROQ_API_KEY:
    groq_client = Groq(api_key=config.GROQ_API_KEY)
    print("✅ Groqクライアント(Llama 3)の準備完了")
else:
    groq_client = None
    print("⚠️ GROQ_API_KEY未設定: Llama 3 バックアップは無効です")


async def generate_response(user_name, conversation_log):
    """
    Generates a response using the Triple Hybrid approach.
    """
    
    prompt = f"""
    あなたはアイドルの「AIまう」です。
    現在、ファンの「{user_name}」さんからメッセージが届きました。

    【会話履歴】
    {conversation_log}

    【指示】
    1. mau_profile.txt の設定（キャラ設定）を守ってください。
    2. 文頭で必ず「{user_name}！」や「{user_name}ちゃん！」と名前を呼んでください。
    3. **相手が英語で話しかけてきた場合は英語で、日本語なら日本語で返信してください。**
       (If the user speaks English, reply in English with the same idol personality.)
    4. 親しい友達のようにタメ口で返信してください。
    5. **返信は「200文字以内」で、Twitterのリプライのように短くテンポよく返してください。長々とした挨拶は省略してOKです。**
    """

    response_text = ""
    used_model = "Gemini 2.5" # For logging
    footer_note = "" # Annotation for user

    try:
        # ---------------------------------------------------
        # ① Gemini 2.5 Flash (Main)
        # ---------------------------------------------------
        if not model_priority:
             raise Exception("Gemini API Key missing")

        print(f"✨ 1. Gemini 2.5 Flash で挑戦中...")
        response = await model_priority.generate_content_async(prompt)
        response_text = response.text
    
    except Exception as e1:
        print(f"⚠️ Gemini 2.5 エラー: {e1}")
        try:
            # ---------------------------------------------------
            # ② Gemini 2.5 Flash Lite (Backup)
            # ---------------------------------------------------
            if not model_backup_1:
                 raise Exception("Gemini API Key missing")

            print("♻️ 2. Gemini 2.5 Lite に切り替えます...")
            response = await model_backup_1.generate_content_async(prompt)
            response_text = response.text
            used_model = "Gemini Lite"
            footer_note = "\n\n(※省エネモード🔋)"
            
        except Exception as e2:
            print(f"⚠️ Gemini Lite エラー: {e2}")
            # ---------------------------------------------------
            # ③ Groq Llama 3 (Fallback)
            # ---------------------------------------------------
            if groq_client:
                print("🔥 3. Groq (Llama 3) 出動！！")
                try:
                    # Call Groq API
                    completion = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", # High performance model
                        messages=[
                            # Inject system setting
                            {"role": "system", "content": CHARACTER_SETTING},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1024,
                    )
                    response_text = completion.choices[0].message.content
                    used_model = "Groq Llama 3"
                    footer_note = "\n\n(※規制モード🚀)"
                    print("✅ Groqで生成成功！")
                    
                except Exception as e3:
                    print(f"❌ Groqもエラー: {e3}")
                    response_text = "ごめんね、今日は回線が全部パンクしちゃったみたい😵‍💫💦 また明日遊ぼうね！"
            else:
                response_text = "ごめんね、ちょっと調子悪いみたい…💦 (Groqキー未設定)"

    print(f"📨 返信モデル: {used_model}")
    
    # Add Dev Indicator
    if config.MAU_ENV == "development":
        footer_note += "\n🛠️ (Dev Check)"

    return response_text + footer_note
