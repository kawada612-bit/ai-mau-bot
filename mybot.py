import discord
import google.generativeai as genai
import os
from dotenv import load_dotenv # ローカル用
from keep_alive import keep_alive

# .envファイルを読み込む（ローカル用・Renderでは無視されます）
load_dotenv()

# ==================================================
# 1. 環境変数の読み込み
# ==================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID_RAW = os.getenv("TARGET_CHANNEL_ID")

try:
    TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_RAW) if TARGET_CHANNEL_ID_RAW else 0
except:
    TARGET_CHANNEL_ID = 0

# ==================================================
# 2. キャラクター設定の読み込み (ここをシンプルに！)
# ==================================================
PROFILE_FILE = "mau_profile.txt"
DEFAULT_PROFILE = "あなたはアイドルの「AIまう」です。明るく親しみやすく振る舞ってください。"

try:
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        PROFILE_DATA = f.read()
    print(f"✅ {PROFILE_FILE} を読み込みました")
except Exception as e:
    print(f"⚠️ プロフィール読み込みエラー: {e}")
    PROFILE_DATA = DEFAULT_PROFILE

# システムプロンプトの構築
CHARACTER_SETTING = f"""
あなたは以下の設定を持つ「AIまう」になりきって発言してください。

{PROFILE_DATA}
"""

# ==================================================
# 3. AIモデルの設定
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    system_instruction=CHARACTER_SETTING
)

# ==================================================
# 4. Discordクライアントの設定
# ==================================================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("=========================================")
    print(f"🚀 起動完了！ログイン名: {client.user}")
    print("=========================================")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    should_reply = False
    
    if client.user in message.mentions:
        should_reply = True
    elif message.channel.id == TARGET_CHANNEL_ID:
        should_reply = True

    if should_reply:
        try:
            async with message.channel.typing():
                # 文脈取得
                history = []
                async for msg in message.channel.history(limit=10):
                    name = "AIまう" if msg.author == client.user else msg.author.display_name
                    clean_content = msg.content.replace(f"<@{client.user.id}>", "").strip()
                    history.append(f"{name}: {clean_content}")
                
                history.reverse()
                conversation_log = "\n".join(history)

                # プロンプト作成
                user_name = message.author.display_name
                
                prompt = f"""
                あなたはアイドルの「AIまう」です。
                現在、ファンの「{user_name}」さんからメッセージが届きました。

                【会話履歴】
                {conversation_log}

                【指示】
                ・mau_profile.txt の設定（リプライモード）を適用してください。
                ・文頭で必ず「{user_name}！」や「{user_name}ちゃん！」と名前を呼んでください。
                ・親しい友達のようにタメ口で返信してください。
                """
                
                response = await model.generate_content_async(prompt)
                await message.reply(response.text, mention_author=False)
                print(f"📨 返信成功: {user_name} へ")

        except Exception as e:
            print(f"❌ エラー発生: {e}")

# ==================================================
# 5. 起動
# ==================================================
keep_alive()

if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("❌ DISCORD_TOKEN がありません")