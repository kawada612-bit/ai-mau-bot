
from src import config
from src import server
from src import bot_client
from src.logger import setup_logger

logger = setup_logger(__name__)

def main() -> None:
    # Start Keep-Alive Server (Flask)
    server.start_server()

    # Run Discord Bot
    if config.DISCORD_TOKEN:
        try:
            bot_client.client.run(config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"❌ 起動エラー: {e}")
    else:
        logger.error("❌ DISCORD_TOKEN がありません")

if __name__ == "__main__":
    main()
