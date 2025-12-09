import discord
import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive
from groq import Groq  # 👈 Groqライブラリ

# ローカル用設定読み込み
load_dotenv()

# ==================================================
# 1. 環境変数の読み込み
# ==================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # 👈 Groqキー
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
# 3. AIモデルの設定 (トリプルハイブリッド構成)
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)

# ① 優先モデル (Gemini 2.5 Flash)
model_priority = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=CHARACTER_SETTING
)

# ② 予備モデル (Gemini 2.5 Flash Lite)
model_backup_1 = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite',
    system_instruction=CHARACTER_SETTING
)

# ③ 最終兵器 (Groq - Llama 3)
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groqクライアント(Llama 3)の準備完了")
else:
    groq_client = None
    print("⚠️ GROQ_API_KEY未設定: Llama 3 バックアップは無効です")

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
    # システムメッセージ（ピン留め通知など）は無視
    if message.is_system():
        return

    # ===============================================================
    # 🧠 反応するかどうかの判定ロジック (アップデート版)
    # ===============================================================
    should_reply = False
    
    # 1. 自分がメンションに含まれているか？
    is_mentioned = client.user in message.mentions
    
    # 2. 他人へのメンションが含まれているか？ (自分以外へのメンションがあるか)
    other_mentions = [user for user in message.mentions if user != client.user]
    has_other_mentions = len(other_mentions) > 0

    if is_mentioned:
        # A. 自分宛てなら、他に誰がいようと絶対に反応する (複数メンション対応)
        should_reply = True
        
    elif message.channel.id == TARGET_CHANNEL_ID:
        # B. 指定チャンネルの場合
        if has_other_mentions:
            # 他の人へのメンションがある場合は、割り込まない (無視)
            should_reply = False
        else:
            # 誰へのメンションもない(=独り言や雑談)なら反応する
            should_reply = True

    # ===============================================================

    if should_reply:
        try:
            async with message.channel.typing():
                # ---------------------------------------------------
                # 📝 会話履歴の作成
                # ---------------------------------------------------
                history = []
                async for msg in message.channel.history(limit=10):
                    if not msg.is_system():
                        name = "AIまう" if msg.author == client.user else msg.author.display_name
                        clean_content = msg.content.replace(f"<@{client.user.id}>", "").strip()
                        history.append(f"{name}: {clean_content}")
                
                history.reverse()
                conversation_log = "\n".join(history)
                user_name = message.author.display_name
                
                # ---------------------------------------------------
                # 📝 プロンプト作成 (全モデル共通)
                # ---------------------------------------------------
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
                
                # ===========================================================
                # 🤖 トリプル・ハイブリッド生成ロジック
                # ===========================================================
                response_text = ""
                used_model = "Gemini 2.5" # ログ用
                footer_note = "" # ユーザーへの注釈
                
                try:
                    # ---------------------------------------------------
                    # ① Gemini 2.5 Flash (メイン)
                    # ---------------------------------------------------
                    print(f"✨ 1. Gemini 2.5 Flash で挑戦中...")
                    response = await model_priority.generate_content_async(prompt)
                    response_text = response.text
                
                except Exception as e1:
                    print(f"⚠️ Gemini 2.5 エラー: {e1}")
                    try:
                        # ---------------------------------------------------
                        # ② Gemini 2.5 Flash Lite (サブ)
                        # ---------------------------------------------------
                        print("♻️ 2. Gemini 2.5 Lite に切り替えます...")
                        response = await model_backup_1.generate_content_async(prompt)
                        response_text = response.text
                        used_model = "Gemini Lite"
                        footer_note = "\n\n(※省エネモード🔋)"
                        
                    except Exception as e2:
                        print(f"⚠️ Gemini Lite エラー: {e2}")
                        # ---------------------------------------------------
                        # ③ Groq Llama 3 (最終兵器)
                        # ---------------------------------------------------
                        if groq_client:
                            print("🔥 3. Groq (Llama 3) 出動！！")
                            try:
                                # Groq API呼び出し
                                completion = groq_client.chat.completions.create(
                                    model="llama-3.3-70b-versatile", # 高性能モデル
                                    messages=[
                                        # システム設定を注入
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

                # -----------------------------------------------------------
                # 📨 送信処理 (2000文字自動分割)
                # -----------------------------------------------------------
                print(f"📨 返信モデル: {used_model}")
                
                # 注釈を結合
                final_text = response_text + footer_note

                if len(final_text) > 2000:
                    for i in range(0, len(final_text), 2000):
                        chunk = final_text[i:i+2000]
                        if i == 0:
                            await message.reply(chunk, mention_author=False)
                        else:
                            await message.channel.send(chunk)
                else:
                    await message.reply(final_text, mention_author=False)
                    
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
