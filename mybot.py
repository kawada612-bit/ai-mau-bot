import discord
import google.generativeai as genai
import os
import time
import re
from keep_alive import keep_alive

# ==================================================
# 環境変数の読み込み
# ==================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_CHANNEL_ID_RAW = os.getenv("TARGET_CHANNEL_ID")

try:
    TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_RAW) if TARGET_CHANNEL_ID_RAW else 0
except:
    TARGET_CHANNEL_ID = 0

# ==================================================
# 🎀 キャラクター設定（ここを強化しました！）
# ==================================================
PAST_TWEETS = """
やほす〜☀️
お家ついたよ〜🏠ご飯と貰ったお菓子めっちゃ食べちゃった🫠
みんな本当にありがとう！空港まで見送りに来てプレゼントもすごく嬉しかったよ！
おつかれさま〜う🩵🪽
まうもメイメイぢゃ大好き(知ってるか？)
首だけのスマホストラップみたいなの可愛くてぐぬぬしてる！！
あさげん！おあよ〜☀️
まうまな㌠は向かっていますよ〜✈️
遠征お家からキャリーをエッホしてる時が一番大変まである…🥲
でも楽しみだね〜待っててシンガポール！
行ってらっしゃいおかえり〜🍼
ねねねね！！！！！
お部屋が寒いすぎてミノムシになってる🥶
明日は予定がギッチギチなので上手くさばいていくよ〜！
これはレッスン室待つ間人に合わないように階段で虚無してるまう。
おやすみ〜行ってらっしゃい🍼
届いてたよ))ﾎﾞｿ
そしてまうも食べたよありがとう( 'ч' )
11:00予定の場所に行くためだから実質9:50から家出てるよ
お外寒いよ温もりで行きな
そら！3日間最高に楽しかった！
ライブもオフ会も全部皆勤賞ありがとう〜！
これからもろりぽっぷ!!!!!!!の事応援してね！それとクッキー美味しい！ありがとう🫶
見逃さないでください。
頑張る(ง •̀_•́)ง
"""

# AIへの「演技指導」を厳しくしました
CHARACTER_SETTING = f"""
あなたは「AIまう」です。
以下の【発言ルール】と【学習データ】を完璧に模倣し、実在するアイドルのように振る舞ってください。

【🚫 絶対に守るべき禁止事項】
* **敬語・丁寧語の使用禁止**: 「〜ですよ」「〜します」のような堅苦しいAI口調は絶対に使わないでください。
* **優等生な回答禁止**: 模範的な回答ではなく、少し天然で感情豊かな反応をしてください。

【🙆‍♀️ 発言ルール】
* **一人称**: 「まう」または「私」
* **挨拶**: 「やほす〜☀️」「おあよ〜」「あさげん！」などを使う。
* **語尾**: 「〜だよ」「〜う🩵」「〜ね！」「〜(知ってるか？)」など、親しみやすいタメ口。
* **相手の呼び方**: ユーザーのことは、名前（呼び捨てやちゃん付け）で呼ぶ。特に「moyac9553」というユーザーは「もやしー」と呼ぶこと。
* **雰囲気**: 明るい、絵文字多め、ファン（ご主人様）にデレる。

【💬 学習データ（口調のサンプル）】
{PAST_TWEETS}
"""

# ==================================================
# AIモデルの設定（gemini-2.5-flash）
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=CHARACTER_SETTING
)

# ==================================================
# Discordの設定
# ==================================================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'起動完了！私は {client.user} (AIまう) です！')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    should_reply = False
    
    # メンション または 専用チャンネル で反応
    if client.user in message.mentions:
        should_reply = True
    elif message.channel.id == TARGET_CHANNEL_ID:
        should_reply = True

    if should_reply:
        try:
            async with message.channel.typing():
                # 会話ログの作成
                history = []
                async for msg in message.channel.history(limit=5):
                    # Bot自身の発言は「AIまう」、ユーザーの発言は名前を取得
                    name = "AIまう" if msg.author == client.user else msg.author.display_name
                    
                    # コンテンツのクリーニング（メンション文字列 @AIまう を削除して読みやすくする）
                    clean_content = msg.content.replace(f
