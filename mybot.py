import discord
import google.generativeai as genai
import os
import random
from keep_alive import keep_alive

# ==================================================
# クラウドの環境変数から鍵を読み込む設定
# ==================================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# エラー回避のため、IDがない場合は0を入れておく
channel_id_str = os.getenv("TARGET_CHANNEL_ID")
TARGET_CHANNEL_ID = int(channel_id_str) if channel_id_str else 0
# ==================================================

# 学習データ（まうちゃんの魂）
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

# キャラクター設定
CHARACTER_SETTING = f"""
あなたは「AIまう」です。
実在するアイドルの発言データを学習して生まれた、お喋りなAIボットです。

【重要なルール】
1. **口調の模倣**: 以下の学習データを元に、独特な挨拶（「やほす〜」「おあよ〜」）や語尾、絵文字の雰囲気を完璧に真似してください。
2. **自己認識**: あなたは「AI」です。ユーザーから正体を聞かれたら「まうちゃんのデータを学習した『AIまう』だよ！よろしくね🩵」と明るく答えてください。
3. **性格**: 明るくて、ファン（ユーザー）に親しみを持って接してください。

【学習データ】
{PAST_TWEETS}
"""

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=CHARACTER_SETTING
)

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
    
    if client.user in message.mentions:
        should_reply = True
    elif message.channel.id == TARGET_CHANNEL_ID:
        should_reply = True

    if should_reply:
        try:
            async with message.channel.typing():
                history = []
                async for msg in message.channel.history(limit=10):
                    history.append(f"{msg.author.display_name}: {msg.content}")
                history.reverse()
                conversation_log = "\n".join(history)
                
                prompt = f"""
                以下の会話の流れを踏まえて、今の会話にふさわしい返事をしてください。
                相手の名前を呼ぶときは、会話ログにある名前を使ってください。
                【直近の会話ログ】
                {conversation_log}
                """
                
                response = await model.generate_content_async(prompt)
                await message.reply(response.text, mention_author=False)

        except Exception as e:
            print(f"エラー: {e}")

# サーバーを起動して常駐させる
keep_alive()
client.run(DISCORD_TOKEN)