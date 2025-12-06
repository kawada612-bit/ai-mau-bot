import discord
import google.generativeai as genai
import os
import time
from keep_alive import keep_alive

# ==================================================
# 1. 環境変数の読み込み
# ==================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID_RAW = os.getenv("TARGET_CHANNEL_ID")

# チャンネルIDを数値に変換（エラー対策）
try:
    TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_RAW) if TARGET_CHANNEL_ID_RAW else 0
except:
    TARGET_CHANNEL_ID = 0

# ==================================================
# 2. キャラクター設定の読み込み (外部ファイル)
# ==================================================
PROFILE_FILE = "mau_profile.txt"
DEFAULT_PROFILE = "あなたはアイドルの「AIまう」です。明るく親しみやすく振る舞ってください。"

try:
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        PROFILE_DATA = f.read()
    print(f"✅ {PROFILE_FILE} を読み込みました")
except Exception as e:
    print(f"⚠️ プロフィール読み込みエラー: {e}")
    print("デフォルト設定を使用します。")
    PROFILE_DATA = DEFAULT_PROFILE

# システムプロンプトの構築
CHARACTER_SETTING = f"""
あなたは以下の設定を持つ「AIまう」になりきって発言してください。

{PROFILE_DATA}
"""

# ==================================================
# 3. AIモデルの設定 (Gemini 2.5 Flash)
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
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
    print(f"参加サーバー数: {len(client.guilds)}")
    print("=========================================")

@client.event
async def on_message(message):
    # 自分自身の発言には反応しない
    if message.author == client.user:
        return

    should_reply = False
    
    # 条件A: メンションされたら反応
    if client.user in message.mentions:
        should_reply = True
    # 条件B: 専用チャンネルなら反応
    elif message.channel.id == TARGET_CHANNEL_ID:
        should_reply = True

    if should_reply:
        try:
            async with message.channel.typing():
                # -------------------------------------------------
                # 文脈（会話履歴）の取得
                # -------------------------------------------------
                history = []
                async for msg in message.channel.history(limit=10):
                    # Bot自身の発言は「AIまう」、ユーザーの発言は表示名を使用
                    name = "AIまう" if msg.author == client.user else msg.author.display_name
                    # メンション文字列（<@1234...>）を削除して読みやすくする
                    clean_content = msg.content.replace(f"<@{client.user.id}>", "").strip()
                    history.append(f"{name}: {clean_content}")
                
                history.reverse() # 古い順に並び替え
                conversation_log = "\n".join(history)

                # -------------------------------------------------
                # プロンプト作成（ここが分析結果を反映した重要ポイント！）
                # -------------------------------------------------
                user_name = message.author.display_name
                
                prompt = f"""
                あなたはアイドルの「AIまう」です。
                現在、ファンの「{user_name}」さんからメッセージが届きました。

                【会話履歴】
                {conversation_log}

                【指示】
                ・mau_profile.txt の「モードA：リプライ」の設定を適用してください。
                ・文頭で必ず「{user_name}！」や「{user_name}ちゃん！」と名前を呼んでください。
                ・相手の発言に対して、友達のように親近感を持って、タメ口で返信してください。
                ・絵文字（🩵、☀️、🍼、🐱、🤣、🥺）を適度に使ってください。
                """
                
                # AIに生成させる
                response = await model.generate_content_async(prompt)
                
                # Discordに返信
                await message.reply(response.text, mention_author=False)
                print(f"📨 返信しました: {user_name} へ")

        except Exception as e:
            print(f"❌ エラー発生: {e}")
            import traceback
            traceback.print_exc() 

# ==================================================
# 5. サーバー維持 & 起動
# ==================================================
keep_alive()
