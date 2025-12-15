
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Discord
DISCORD_TOKEN: Optional[str] = os.getenv("DISCORD_TOKEN")

# AI API Keys
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")

# Supabase
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

# Target Channel
TARGET_CHANNEL_ID_RAW = os.getenv("TARGET_CHANNEL_ID")
try:
    TARGET_CHANNEL_ID: int = int(TARGET_CHANNEL_ID_RAW) if TARGET_CHANNEL_ID_RAW else 0
except ValueError:
    TARGET_CHANNEL_ID: int = 0

# Environment Mode (production / development)
MAU_ENV: str = os.getenv("MAU_ENV", "production")

# File Paths
# Construct absolute paths to ensure they work regardless of where the script is run from
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR: str = os.path.join(BASE_DIR, "data")
PROFILE_FILE_PATH: str = os.path.join(DATA_DIR, "mau_profile.txt")

# Default Persona
DEFAULT_PROFILE: str = "あなたはアイドルの「AIまう」です。明るく親しみやすく振る舞ってください。"

# CORS Configuration
ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",")] if ALLOWED_ORIGINS_RAW != "*" else ["*"]
