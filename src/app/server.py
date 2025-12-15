
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
import httpx
import os
import json
import time
from datetime import datetime

from src.app import bot
from src.core import config
from src.core.logger import setup_logger
from src.services.ogp_service import OGPService

logger = setup_logger(__name__)

class MessageHistory(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'ai'")
    text: str = Field(..., description="Message text")

class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Message text (1-500 chars)")
    user_name: str = Field(default="Guest", max_length=50, description="User name (max 50 chars)")
    history: list[MessageHistory] = Field(default=[], description="Recent conversation history (up to 12 messages)")
    timezone: str = Field(default="Asia/Tokyo", description="User's timezone (e.g. Asia/Tokyo)")

class ChatResponse(BaseModel):
    response: str
    mode: str = Field(default="unknown", description="The mode/model used for generation (reflex, genius, speed, main, backup)")


class OGPRequest(BaseModel):
    url: str = Field(..., description="URL to fetch OGP metadata from")

class OGPResponse(BaseModel):
    title: str
    description: str
    image: str

# Global variables to hold tasks
bot_task = None
self_ping_task = None

async def self_ping():
    """自己Ping機能: 15分ごとに自分自身にアクセスしてスリープを防ぐ"""
    # RENDER環境でのみ動作（ローカル開発では不要）
    if not os.getenv("RENDER"):
        logger.info("⏭️ Self-ping disabled (not in RENDER environment)")
        return
    
    # RenderのサービスURLを取得
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_external_url:
        logger.warning("⚠️ RENDER_EXTERNAL_URL not found, self-ping disabled")
        return
    
    health_url = f"{render_external_url}/health"
    logger.info(f"🏓 Self-ping enabled: {health_url}")
    
    await asyncio.sleep(60)  # 起動後1分待機
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            try:
                response = await client.get(health_url)
                if response.status_code == 200:
                    logger.info("✅ Self-ping successful")
                else:
                    logger.warning(f"⚠️ Self-ping returned {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Self-ping failed: {e}")
            
            # 14分待機（15分より少し短めに設定）
            await asyncio.sleep(14 * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task, self_ping_task
    # Startup
    logger.info("🚀 Starting Discord Bot via FastAPI lifespan...")
    if config.DISCORD_TOKEN:
        # Hold the task reference to prevent garbage collection
        bot_task = asyncio.create_task(bot.client.start(config.DISCORD_TOKEN))
    else:
        logger.error("❌ DISCORD_TOKEN is missing!")
    
    # Start self-ping task
    logger.info("🏓 Starting self-ping task...")
    self_ping_task = asyncio.create_task(self_ping())
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Discord Bot...")
    if bot.client:
        await bot.client.close()
    
    # Cancel self-ping task
    if self_ping_task:
        self_ping_task.cancel()
        try:
            await self_ping_task
        except asyncio.CancelledError:
            pass
    
    # Wait for the bot task to finish if needed (optional)
    if bot_task:
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="AI Mau API", lifespan=lifespan)

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "AI Mau Bot API is running", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

def build_conversation_log(user_name: str, history: list[MessageHistory], current_text: str) -> str:
    """会話履歴を整形してAIに渡す形式に変換"""
    log_lines = []
    
    for msg in history:
        if msg.role == 'user':
            log_lines.append(f"{user_name}: {msg.text}")
        else:
            log_lines.append(f"AIまう: {msg.text}")
    
    # 現在のメッセージを追加
    log_lines.append(f"{user_name}: {current_text}")
    
    return "\n".join(log_lines)

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, req: ChatRequest):
    start_time = time.time()
    used_model = "Unknown"
    error_msg = None
    
    try:
        # Build conversation log from history
        conversation_log = build_conversation_log(req.user_name, req.history, req.text)
        logger.info(f"📝 Conversation history: {len(req.history)} messages")
        
        # ---------------------------------------------------
        # 🤖 High-IQ Analytics Flow (Same as Discord Bot)
        # ---------------------------------------------------
        ANALYTICS_KEYWORDS = ['いつ', '予定', 'スケジュール', 'ライブ', 'イベント', '何回', '件数', '分析', '教えて']
        context_info = None
        
        if any(k in req.text for k in ANALYTICS_KEYWORDS):
            logger.info("🧠 Analytics Keyword Detected in API. Generating SQL...")
            try:
                # Reuse the same brain and analytics instance from bot module
                sql = await bot.brain.generate_sql(req.text, bot.analytics.get_schema_info())
                result_md = bot.analytics.execute_query(sql)
                context_info = result_md
                logger.info("📊 Analysis Result: " + str(context_info)[:50] + "...")
            except Exception as e:
                logger.error(f"Analytics Error: {e}")

        # Need to capture which model was used.
        # Since currently generate_response returns string, we might need to parse logs or adjust return type.
        # For now, we assume the logger in ai_service outputs the model info.
        # Ideally, we should refactor generate_response to return metadata.
        # Observing logs from ai_service: "📨 返信モデル: {used_model}"
        
        response_text, mode = await asyncio.wait_for(
            bot.brain.generate_response(req.user_name, conversation_log, context_info, req.timezone),
            timeout=30.0
        )
        
        return ChatResponse(response=response_text, mode=mode)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ API Chat Error: {e}")
        # Return 500 Internal Server Error with detail
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Structured Logging
        duration = time.time() - start_time
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "chat_request",
            "ip": request.client.host,
            "user_name": req.user_name,
            "message_length": len(req.text),
            "response_time": round(duration, 3),
            "success": error_msg is None,
            "error": error_msg
        }
        # Use a special prefix for easier parsing or just log as info
        logger.info(f"ANALYTICS: {json.dumps(log_entry)}")

@app.post("/api/ogp", response_model=OGPResponse)
async def ogp_endpoint(req: OGPRequest):
    """Fetch OGP metadata for a given URL."""
    try:
        ogp_data = await OGPService.fetch_ogp(req.url)
        
        # If OGP fetch fails, return empty data instead of error
        # This allows the frontend to gracefully fallback to simple link card
        if ogp_data is None:
            logger.warning(f"⚠️ OGP fetch failed for {req.url}, returning empty data")
            return OGPResponse(
                title='',
                description='',
                image=''
            )
        
        return OGPResponse(
            title=ogp_data.get('title', ''),
            description=ogp_data.get('description', ''),
            image=ogp_data.get('image', '')
        )
    except Exception as e:
        logger.error(f"❌ OGP API Error: {e}")
        # Return empty data instead of error for better UX
        return OGPResponse(
            title='',
            description='',
            image=''
        )
