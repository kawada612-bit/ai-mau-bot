
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
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
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from supabase import create_client

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
    suggestions: list[str] = Field(default=[], description="Suggested follow-up messages for the user")


class OGPRequest(BaseModel):
    url: str = Field(..., description="URL to fetch OGP metadata from")

class OGPResponse(BaseModel):
    title: str
    description: str
    image: str

# Global variables to hold tasks
bot_task = None
self_ping_task = None

# Schedule sync - concurrency control
_sync_in_progress = False
_sync_lock = threading.Lock()
_sync_executor = ThreadPoolExecutor(max_workers=1)

def _run_sync_with_safeguards():
    """Execute schedule sync with error handling"""
    global _sync_in_progress
    try:
        from src.workers.scheduler import fetch_and_sync
        logger.info("🔄 Starting schedule sync...")
        fetch_and_sync(dry_run=False)
        logger.info("✅ Schedule sync completed successfully")
    except Exception as e:
        logger.error(f"❌ Schedule sync failed: {e}")
    finally:
        with _sync_lock:
            _sync_in_progress = False

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
        
        response_text, mode, suggestions = await asyncio.wait_for(
            bot.brain.generate_response(req.user_name, conversation_log, context_info, req.timezone),
            timeout=30.0
        )
        
        return ChatResponse(response=response_text, mode=mode, suggestions=suggestions)
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

@app.api_route("/api/sync-schedule", methods=["GET", "HEAD"])
async def sync_schedule_endpoint(token: str = ""):
    """Trigger schedule sync (for UptimeRobot scheduled calls)"""
    global _sync_in_progress
    
    # Token authentication
    if token != config.SYNC_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if sync is already in progress
    with _sync_lock:
        if _sync_in_progress:
            return {"status": "skipped", "message": "Sync already in progress"}
        _sync_in_progress = True
    
    # Execute in background with ThreadPoolExecutor
    _sync_executor.submit(_run_sync_with_safeguards)
    
    return {"status": "started", "message": "Schedule sync started in background"}

@app.api_route("/api/schedules", methods=["GET", "HEAD"])
@limiter.exempt
async def get_schedules(response: Response, request: Request, since: Optional[str] = None, until: Optional[str] = None):
    """
    Get schedules from Supabase for Gemini Gems.
    - since: YYYYMMDD (optional, defaults to today)
    - until: YYYYMMDD (optional)
    """
    # CORS relaxation override for this specific endpoint
    # Force Access-Control-Allow-Origin to * regardless of config
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    # Support for HEAD requests (Gems health check/reachability)
    if request.method == "HEAD":
        return Response(status_code=200, headers=dict(response.headers))

    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        query = supabase.table("schedules").select("*")
        
        # Parse 'since', default to today
        if since:
            try:
                parsed_since = datetime.strptime(since, "%Y%m%d")
                since_iso = parsed_since.strftime("%Y-%m-%dT00:00:00")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' format. Use YYYYMMDD.")
        else:
            # Fallback to today
            today = datetime.now()
            since_iso = today.strftime("%Y-%m-%dT00:00:00")
            
        # Add gte condition
        query = query.gte("start_at", since_iso)
        
        # Parse 'until' if provided
        if until:
            try:
                parsed_until = datetime.strptime(until, "%Y%m%d")
                # Include the whole day of 'until'
                until_iso = parsed_until.strftime("%Y-%m-%dT23:59:59")
                query = query.lte("start_at", until_iso)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'until' format. Use YYYYMMDD.")
                
        # Execute query
        response = query.order("start_at").execute()
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ /api/schedules Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
