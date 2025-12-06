import discord
import google.generativeai as genai
import os
from keep_alive import keep_alive

# --- 診断用ログ出力 ---
print("=== システム起動開始 ===")

# 環境変数の読み込み確認
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
channel_id_str = os.getenv("TARGET_CHANNEL_ID")

print(f"環境変数の確認: TARGET_CHANNEL_ID = '{channel_id_str}'")

if not DISCORD_TOKEN:
    print("【重大エラー】DISCORD_TOKEN が読み込めません！")
if not GEMINI_API_KEY:
    print("【重大エラー】GEMINI_API_KEY が読み込めません！")

# チャンネルIDの変換
try:
    TARGET_CHANNEL_ID = int(channel_id_str)
    print(f"ID変換成功: {TARGET_CHANNEL_ID}")
except Exception as e:
    TARGET_CHANNEL_ID = 0
    print(f"【注意】チャンネルIDが数字ではありません。ID指定機能は無効化されます。元データ: {channel_id_str}")

# --- ここからいつもの設定 ---

# キャラ設定（省略せずに記述）
PAST_TWEETS = "（学習データ省略）" 
CHARACTER_SETTING = "あなたはAIまうです。"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=CHARACTER_SETTING
)

intents = discord.Intents.default()
intents.message_content = True # ここが重要
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"=== 接続成功！ ===")
    print(f"Bot名: {client.user} (ID: {client.user.id})")
    print(f"所属サーバー数: {len(client.guilds)}")
    print("=======================")

@client.event
async def on_message(message):
    # ロボット自身の発言は無視（ログには出す）
    if message.author == client.user:
        return

    # ★ここが診断ポイント：受け取った全てのメッセージをログに出す
    print(f"\n[受信] チャンネルID: {message.channel.id} / 送信者: {message.author} / 内容: {message.content}")

    should_reply = False
    reason = ""

    # 判定ロジックのログ出し
    if client.user in message.mentions:
        should_reply = True
        reason = "メンション検知"
    elif message.channel.id == TARGET_CHANNEL_ID:
        should_reply = True
        reason = "専用チャンネルID一致"
    else:
        reason = f"反応条件不一致 (Target: {TARGET_CHANNEL_ID} != Current: {message.channel.id})"

    print(f"判定結果: {should_reply} (理由: {reason})")

    if should_reply:
        try:
            print("AI生成を開始します...")
            async with message.channel.typing():
                prompt = f"返事をしてください。\nユーザーの発言: {message.content}"
                response = await model.generate_content_async(prompt)
                print(f"AI生成完了。返信します: {response.text[:20]}...")
                await message.reply(response.text, mention_author=False)
                print("返信送信完了")
        except Exception as e:
            print(f"【エラー発生】処理中にエラー: {e}")

# サーバー維持
keep_alive()
try:
    client.run(DISCORD_TOKEN)
except Exception as e:
    print(f"【起動エラー】: {e}")
