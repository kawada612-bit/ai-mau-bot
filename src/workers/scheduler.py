
import time
import json
import sys
import argparse
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional
from playwright.sync_api import sync_playwright
from supabase import create_client
from groq import Groq
from src.core import config
from src.core.logger import setup_logger

logger = setup_logger(__name__)

# 定数
TIMETREE_BASE_URL: str = "https://timetreeapp.com/public_calendars/lollipop_1116"

# Groq初期化
groq_client: Optional[Groq] = None
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

def extract_details_with_groq(title: str, date_str: str, note: str) -> dict:
    """Groq (Llama 3) でメモ欄から詳細情報（時間、場所、チケット、料金、特典）を抽出"""
    if not note or not groq_client: return {}
    
    prompt = f"""
    You are a precise data extraction engine.
    Extract information from the text **exactly as it appears** in the source.

    [Input]
    Date: {date_str}
    Title: {title}
    Note: {note}

    [Rules]
    1. Output JSON ONLY.
    2. **ticket_url**: Extract ticket links. Look for domains like 'livepocket.jp', 't.livepocket.jp', 't-dv.com', 'tiget.net' even if 'https://' is missing. If missing protocol, prepend 'https://'.
    3. **price**: Extract ticket price details. KEEP ORIGINAL TEXT. Do NOT translate '¥' to '元' or 'Yuan'. Do NOT change currency symbols.
    4. **bonus**: Extract text related to '特典', '招待', '写メ', 'チェキ', '動画', 'くじ', 'プレゼント'.
    5. **place**: Venue name (e.g. "SHIBUYA CYCLONE").
    
    6. **start_at/end_at**:
       - Extract START/END times (ISO 8601: YYYY-MM-DDTHH:MM:SS+09:00).
       - Handle "1040" as "10:40".
       - If "OPEN" and "START" exist, use "START" for start_at. If only "OPEN", use "OPEN".
       - If time is "TBA" or unknown, return null for times.

    Output Schema:
    {{
       "start_at": "ISO string or null",
       "end_at": "ISO string or null",
       "place": "string or null",
       "ticket_url": "string or null",
       "price": "string or null",
       "bonus": "string or null"
    }}
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
        return json.loads(content)
    except Exception as e:
        logger.warning(f"AI解析エラー: {e}")
        return {}

def fetch_and_sync(dry_run: bool = False) -> None:
    if not check_env_vars(): return
    
    logger.info(f"🚀 同期プロセスを開始します (モード: {'Dry Run' if dry_run else '通常実行'})...")
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

        # 今月から向こう4ヶ月分を巡回
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

    # 既存データの更新日時を取得して、変更がないものはスキップするようにする
    existing_updates = {}
    supabase = None
    if config.SUPABASE_URL and config.SUPABASE_KEY:
        try:
            supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            # 全件取得してIDと更新日時をマッピング
            response = supabase.table("schedules").select("source_id, updated_at").execute()
            existing_updates = {item["source_id"]: item["updated_at"] for item in response.data}
        except Exception as e:
            logger.warning(f"⚠️ 既存データの取得失敗 (初回実行時は正常): {e}")

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
            
            updated_at_iso = updated_at_dt.isoformat()
            dt_obj = datetime.fromtimestamp(raw_start, timezone(timedelta(hours=9)))

            # 変更チェック: すでにDBにあり、更新日時が変わっていなければ解析をスキップ
            if source_id in existing_updates:
                try:
                    db_updated_at = existing_updates[source_id]
                    # Supabaseの日時は '2026-03-06T14:06:02.365+00' のような形式
                    # Pythonのisoformatは '2026-03-06T14:06:02.365000+00:00'
                    # 両方を datetime オブジェクトにして比較
                    dt1 = datetime.fromisoformat(db_updated_at.replace('Z', '+00:00'))
                    dt2 = datetime.fromisoformat(updated_at_iso)
                    
                    if dt1 == dt2:
                        logger.info(f"  ⏭️  スキップ (変更なし): {title[:15]}...")
                        continue
                except Exception as e:
                    logger.debug(f"比較エラー: {e}")
            start_at = dt_obj.isoformat()
            end_at = None
            is_all_day = event.get("all_day", False)
            
            place = None
            ticket_url = None
            price_details = None
            bonus = None

            # AI補正
            if note and groq_client:
                extracted = extract_details_with_groq(title, dt_obj.strftime('%Y-%m-%d'), note)
                
                ai_start = extracted.get("start_at")
                ai_end = extracted.get("end_at")
                place = extracted.get("place")
                ticket_url = extracted.get("ticket_url")
                price_details = extracted.get("price")
                bonus = extracted.get("bonus")

                if ai_start:
                    # 日付整合性チェック
                    original_date = dt_obj.date()
                    try:
                        ai_dt = datetime.fromisoformat(ai_start)
                        ai_date = ai_dt.date()
                        
                        if original_date != ai_date:
                            logger.warning(f"⚠️ AI Date Mismatch! Skipping AI result. Original: {original_date}, AI: {ai_date}")
                            # フォールバック: AI結果を破棄して元の時間を使用
                        else:
                            start_at = ai_start
                            is_all_day = False
                            if ai_end: end_at = ai_end
                            logger.info(f"  🤖 AI解析成功: {title[:15]}... -> {ai_start} | 📍 {place} | 🎫 {price_details} | 🎁 {bonus}")
                            time.sleep(0.3)
                    except ValueError:
                        logger.warning(f"⚠️ AI returned invalid date format: {ai_start}")
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
                "updated_at": updated_at_dt.isoformat(),
                "place": place,
                "ticket_url": ticket_url,
                "price_details": price_details,
                "bonus": bonus
            })
        except Exception as e:
            logger.error(f"⚠️ データ変換エラー: {e}")

    if upsert_data:
        if dry_run:
            logger.info(f"[Dry Run] Would upsert {len(upsert_data)} items:")
            logger.info(json.dumps(upsert_data, indent=2, default=str))
        else:
            try:
                if supabase:
                    supabase.table("schedules").upsert(upsert_data, on_conflict="source_id").execute()
                    logger.info(f"✅ 同期完了！ {len(upsert_data)} 件を新規保存または更新しました。")
                else:
                    logger.error("Supabase client is not initialized")
            except Exception as e:
                logger.error(f"❌ DB保存エラー: {e}")
    else:
        logger.warning("⚠️ 保存データなし")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scheduler Worker")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without writing to DB")
    args = parser.parse_args()
    
    fetch_and_sync(dry_run=args.dry_run)
    sys.exit(0)
