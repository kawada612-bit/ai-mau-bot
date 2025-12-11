import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

def fetch_history_final():
    base_url = "https://timetreeapp.com/public_calendars/lollipop_1116"
    
    # ==========================================
    # 🎯 設定: 取得したい年
    # ==========================================
    TARGET_YEAR = 2024
    
    print(f"🚀 {TARGET_YEAR}年のデータを収集します（ブラウザ自動操作）...")
    
    all_events = {} # 重複除去のため辞書で管理 (id -> event)

    with sync_playwright() as p:
        # ⚠️ headless=True だとTimeTree側が警戒する場合があるので
        # うまくいかない時は headless=False (画面表示) を試してください
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # -------------------------------------------------------
        # 🕵️‍♀️ 通信傍受 (Network Sniffing)
        # ページ移動中に "public_events" APIが呼ばれたらデータを確保する
        # -------------------------------------------------------
        def handle_response(response):
            # APIのURLパターンに一致し、かつ成功(200)したもの
            if "public_events" in response.url and response.status == 200:
                try:
                    data = response.json()
                    events = data.get("public_events", [])
                    
                    if events:
                        # print(f"  ⚡️ API反応あり: {len(events)}件")
                        for event in events:
                            # IDをキーにして保存（月またぎで重複して取れることがあるため）
                            all_events[event["id"]] = event
                except:
                    pass

        page.on("response", handle_response)

        # -------------------------------------------------------
        # 🗓 カレンダーを1ヶ月ずつめくる
        # -------------------------------------------------------
        for month in range(1, 13):
            # 魔法のパラメータ: ?monthly=2024-01-01
            target_date = f"{TARGET_YEAR}-{month:02d}-01"
            target_page_url = f"{base_url}?monthly={target_date}"
            
            print(f"   📅 {month}月のカレンダーを開いています... ", end="", flush=True)
            
            try:
                # ページへ移動 (これで勝手にAPIが叩かれる)
                page.goto(target_page_url, wait_until="networkidle")
                
                # 念のため少し待つ (データ受信完了待ち)
                # time.sleep(1) 
                
                print("OK")
                
            except Exception as e:
                print(f"⚠️ タイムアウト ({e})")

        browser.close()

    # ==========================================
    # 📊 結果発表
    # ==========================================
    events_list = list(all_events.values())
    
    if not events_list:
        print("\n❌ イベントが1件も取れませんでした。")
        return

    # 日付順にソート
    events_list.sort(key=lambda x: x["start_at"])

    print(f"\n🎉 大勝利！ {TARGET_YEAR}年は合計 {len(events_list)} 件のイベントがありました！\n")
    
    # 集計
    monthly_count = {}
    for event in events_list:
        start_at = event.get("start_at")
        title = event.get("title")
        if start_at:
            dt = datetime.fromtimestamp(start_at / 1000)
            m_key = dt.strftime("%Y-%m")
            monthly_count[m_key] = monthly_count.get(m_key, 0) + 1
            
            # デバッグ: 最初の数件を表示
            # print(f"{dt.strftime('%Y/%m/%d')}: {title}")

    print("📊 月別レポート:")
    for m in sorted(monthly_count.keys()):
        print(f"  {m}: {monthly_count[m]} 回")
    
    print(f"\n合計: {len(events_list)} 回")

if __name__ == "__main__":
    fetch_history_final()