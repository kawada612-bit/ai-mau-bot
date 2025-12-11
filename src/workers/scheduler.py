
import time
import json
import sys
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from playwright.sync_api import sync_playwright
from supabase import create_client
from groq import Groq
from src.core import config
from src.core.logger import setup_logger

logger = setup_logger(__name__)

# 定数
TIMETREE_BASE_URL: str = "https://timetreeapp.com/public_calendars/lollipop_1116"

# Groq初期化
groq_client: Groq | None = None
if config.GROQ_API_KEY:
    groq_client = Groq(api_key=config.GROQ_API_KEY)

def check_env_vars() -> bool:
    """環境変数の設定状況を確認"""
    logger.info("--- ⚙️ 設定チェック ---")
    logger.info(f"Supabase URL : {'✅ OK' if config.SUPABASE_URL else '❌ Missing'}")
    logger.info(f"Supabase Key : {'✅ OK' if config.SUPABASE_KEY else '❌ Missing'}")
    logger.info(f"Groq Key     : {'✅ OK' if config.GROQ_API_KEY else '❌ Missing'}")
    logger.info("-----------------------")
    return bool(config.SUPABASE_URL and config.SUPABASE_KEY)

def refine_time_with_groq(title: str, date_str: str, note: str) -> tuple[str | None, str | None]:
    """Groq (Llama 3) でメモ欄から時間を抽出"""
    if not note or not groq_client: return None, None
    
    prompt = f"""
    You are a scheduler assistant. Extract START and END times from the text.
    
    [Input]
    Date: {date_str}
    Title: {title}
    Note: {note}

    [Rules]
    1. Output JSON: {{ "start_at": "YYYY-MM-DDTHH:MM:SS+09:00", "end_at": "..." or null }}
    2. Handle "1040" as "10:40".
    3. If "OPEN" and "START" exist, use "START". If only "OPEN", use "OPEN".
    4. If time is "TBA" or unknown, return null for both.
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content or "{}"
        data = json.loads(content)
        return data.get("start_at"), data.get("end_at")
    except Exception as e:
        logger.warning(f"AI解析エラー: {e}")
        return None, None

def fetch_and_sync() -> None:
    if not check_env_vars(): return
    
    logger.info("🚀 同期プロセスを開始します (強制実行モード)...")
    all_events = {}

    with sync_playwright() as p:
        logger.info("🌍 ブラウザ起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            if "public_events" in response.url and response.status == 200:
                try:
                    data = response.json()
                    events = data.get("public_events", [])
                    for e in events:
                        all_events[e["id"]] = e
                except: pass

        page.on("response", handle_response)

        # 今月から向こう4ヶ月分をシンプルに巡回
        today = datetime.now()
        for i in range(4):
            target_date = today + relativedelta(months=i)
            date_param = target_date.strftime("%Y-%m-01")
            url = f"{TIMETREE_BASE_URL}?monthly={date_param}"
            
            logger.info(f"🔄 巡回: {date_param} ...")
            try:
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(1500)
            except Exception as e:
                logger.warning(f"⚠️ タイムアウト: {e}")

        browser.close()

    if not all_events:
        logger.warning("❌ データが見つかりませんでした。")
        return

    # データ整形と保存
    upsert_data = []
    events_list = list(all_events.values())
    logger.info(f"📦 合計 {len(events_list)} 件のイベントを処理中...")

    for event in events_list:
        try:
            source_id = str(event["id"])
            title = event.get("title", "")
            note = event.get("note", "")
            raw_start = event["start_at"] / 1000
            
            # 更新日時の取得
            raw_updated_at = event.get("updated_at")
            if raw_updated_at:
                updated_at_dt = datetime.fromtimestamp(raw_updated_at / 1000, timezone.utc)
            else:
                updated_at_dt = datetime.now(timezone.utc)

            dt_obj = datetime.fromtimestamp(raw_start, timezone(timedelta(hours=9)))
            start_at = dt_obj.isoformat()
            end_at = None
            is_all_day = event.get("all_day", False)

            # AI補正
            if note and groq_client:
                # Same-line progress logging not ideal with standard logging, changing to minimal log
                # logger currently adds newlines.
                # Just log finding
                ai_start, ai_end = refine_time_with_groq(title, dt_obj.strftime('%Y-%m-%d'), note)
                
                if ai_start:
                    start_at = ai_start
                    is_all_day = False
                    if ai_end: end_at = ai_end
                    logger.info(f"  🤖 AI解析成功: {title[:15]}... -> {ai_start}")
                    time.sleep(0.3)
                else:
                    logger.debug(f"  🤖 AI解析スキップ: {title[:15]}...")

            upsert_data.append({
                "source_id": source_id,
                "title": title,
                "start_at": start_at,
                "end_at": end_at,
                "description": note,
                "url": event.get("url", ""),
                "image_url": None,
                "is_all_day": is_all_day,
                "updated_at": updated_at_dt.isoformat()
            })
        except Exception as e:
            logger.error(f"⚠️ データ変換エラー: {e}")

    if upsert_data:
        try:
            if config.SUPABASE_URL and config.SUPABASE_KEY:
                supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                supabase.table("schedules").upsert(upsert_data, on_conflict="source_id").execute()
                logger.info(f"✅ 同期完了！ {len(upsert_data)} 件を保存しました。")
            else:
                logger.error("Supabase config failed")
        except Exception as e:
            logger.error(f"❌ DB保存エラー: {e}")
    else:
        logger.warning("⚠️ 保存データなし")

if __name__ == "__main__":
    fetch_and_sync()
