
from src import config
from src import server
from src import bot_client

def main():
    # Start Keep-Alive Server (Flask)
    server.start_server()

    # Run Discord Bot
    if config.DISCORD_TOKEN:
        bot_client.client.run(config.DISCORD_TOKEN)
    else:
        print("❌ DISCORD_TOKEN がありません")

if __name__ == "__main__":
    main()
