
import discord
from src import config
from src.ai import core

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
    # Ignore system messages (pinned notifications, etc.)
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
        
    elif message.channel.id == config.TARGET_CHANNEL_ID:
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
                # 📝 Generate Conversation History
                # ---------------------------------------------------
                history = []
                async for msg in message.channel.history(limit=10):
                    if not msg.is_system():
                        name = "AIまう" if msg.author == client.user else msg.author.display_name
                        # Remove mention to self from content to avoid confusion
                        clean_content = msg.content.replace(f"<@{client.user.id}>", "").strip()
                        history.append(f"{name}: {clean_content}")
                
                history.reverse()
                conversation_log = "\n".join(history)
                user_name = message.author.display_name
                
                # ---------------------------------------------------
                # 🤖 Generate Response (Triple Hybrid)
                # ---------------------------------------------------
                final_text = await core.generate_response(user_name, conversation_log)

                # ---------------------------------------------------
                # 📨 Send Response (Auto-split 2000 chars)
                # ---------------------------------------------------
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
