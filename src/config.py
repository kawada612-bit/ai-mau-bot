
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# AI API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Target Channel
TARGET_CHANNEL_ID_RAW = os.getenv("TARGET_CHANNEL_ID")
try:
    TARGET_CHANNEL_ID = int(TARGET_CHANNEL_ID_RAW) if TARGET_CHANNEL_ID_RAW else 0
except ValueError:
    TARGET_CHANNEL_ID = 0

# Environment Mode (production / development)
MAU_ENV = os.getenv("MAU_ENV", "production")

# File Paths
# Construct absolute paths to ensure they work regardless of where the script is run from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILE_FILE_PATH = os.path.join(DATA_DIR, "mau_profile.txt")

# Default Persona
DEFAULT_PROFILE = "あなたはアイドルの「AIまう」です。明るく親しみやすく振る舞ってください。"
