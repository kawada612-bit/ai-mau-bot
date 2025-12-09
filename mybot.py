import discord
import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

# ローカル用設定読み込み
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
# 2. キャラクター設定の読み込み
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

CHARACTER_SETTING = f"""
あなたは以下の設定を持つ「AIまう」になりきって発言してください。
{PROFILE_DATA}
"""

# ==================================================
# 3. AIモデルの設定 (ハイブリッド構成)
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)

# 優先モデル (最新・最強)
model_priority = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=CHARACTER_SETTING
)

# 予備モデル (軽量・別枠)
model_backup = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
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
    # -----------------------------------------------------------
    # 🛡️ フィルタリング（自分自身 & システムメッセージを無視）
    # -----------------------------------------------------------
    if message.author == client.user:
        return
    
    # これで「ピン留め」などの通知に反応しなくなります
    if message.is_system():
        return
    
    should_reply = False
    if client.user in message.mentions:
        should_reply = True
    elif message.channel.id == TARGET_CHANNEL_ID:
        should_reply = True

    if should_reply:
        try:
            async with message.channel.typing():
                history = []
                async for msg in message.channel.history(limit=10):
                    name = "AIまう" if msg.author == client.user else msg.author.display_name
                    clean_content = msg.content.replace(f"<@{client.user.id}>", "").strip()
                    history.append(f"{name}: {clean_content}")
                
                history.reverse()
                conversation_log = "\n".join(history)

                user_name = message.author.display_name
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
                """
                
                # ===========================================================
                # 🤖 エラーハンドリング付き生成ロジック
                # ===========================================================
                response_text = ""
                error_footer = "" 
                
                try:
                    # ① まず優先モデル(2.5)で挑戦
                    print(f"✨ 2.5-Flash(優先)で生成中...")
                    response = await model_priority.generate_content_async(prompt)
                    response_text = response.text
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"⚠️ 優先モデルエラー発生: {error_msg}")

                    if "429" in error_msg or "ResourceExhausted" in error_msg:
                        print("📉 原因: リミット切れ")
                        # error_footer = "\n\n(⚠️ API制限がかかったから、予備モデルに切り替えたよ！)"
                    elif "404" in error_msg:
                        print("📉 原因: モデル不明")
                        error_footer = "\n\n(⚠️ モデルが見つからないエラーが出たから、予備モデルを使うね！)"
                    else:
                        error_footer = "\n\n(⚠️ メインモデルでエラーが出たから、予備モデルで対応するね！)"

                    # ② 予備モデル(1.5系)で再挑戦
                    print("♻️ 予備モデルに切り替えます...")
                    try:
                        response = await model_backup.generate_content_async(prompt)
                        response_text = response.text + error_footer
                        print("✅ 予備モデルで成功しました")
                        
                    except Exception as e2:
                        # ③ 予備モデルもダメだった場合
                        print(f"❌ 予備モデルもエラー: {e2}")
                        
                        if "429" in str(e2):
                            response_text = "APIのリミットを使い切っちゃったみたい！😭\n今日はもう動けないから、また明日遊ぼうね〜💦 (Quota Exceeded)"
                        elif "Safety" in str(e2) or "Blocked" in str(e2):
                            response_text = "その内容はAIの安全フィルターに引っかかっちゃった！言えないよ〜🙅‍♀️ (Safety Block)"
                        else:
                            response_text = "システムエラーが発生したよ！ログを確認してね💦 (Internal Server Error)"

                # Discordに返信
                await message.reply(response_text, mention_author=False)
                print(f"📨 返信完了: {user_name} へ")

        except Exception as e:
            print(f"❌ 致命的なエラー: {e}")

# ==================================================
# 5. 起動
# ==================================================
keep_alive()

if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print("❌ DISCORD_TOKEN がありません")