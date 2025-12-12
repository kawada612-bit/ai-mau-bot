
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio

from src.app import bot
from src.core import config
from src.core.logger import setup_logger

logger = setup_logger(__name__)

class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Message text cannot be empty")
    user_name: str = "Guest"

class ChatResponse(BaseModel):
    response: str

# Global variable to hold the bot task
bot_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task
    # Startup
    logger.info("🚀 Starting Discord Bot via FastAPI lifespan...")
    if config.DISCORD_TOKEN:
        # Hold the task reference to prevent garbage collection
        bot_task = asyncio.create_task(bot.client.start(config.DISCORD_TOKEN))
    else:
        logger.error("❌ DISCORD_TOKEN is missing!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Discord Bot...")
    if bot.client:
        await bot.client.close()
    
    # Wait for the task to finish if needed (optional)
    if bot_task:
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="AI Mau API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        # Construct a simple conversation log for the AI
        conversation_log = f"{req.user_name}: {req.text}"
        
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

        # Generate response using the existing bot brain
        # response_text = await bot.brain.generate_response(
        #     req.user_name, 
        #     conversation_log
        # )
        
        # 30秒タイムアウト設定 (bot.pyと同様)
        response_text = await asyncio.wait_for(
            bot.brain.generate_response(req.user_name, conversation_log, context_info),
            timeout=30.0
        )
        
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"❌ API Chat Error: {e}")
        # Return 500 Internal Server Error with detail
        raise HTTPException(status_code=500, detail=str(e))
