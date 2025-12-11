import requests
import json
import datetime
from bs4 import BeautifulSoup

# ターゲット: ろりぽっぷ!!!!!!! 公開カレンダー
TARGET_URL = "https://timetreeapp.com/public_calendars/lollipop_1116"

def check_timetree():
    print(f"🔄 アクセス中: {TARGET_URL} ...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        res = requests.get(TARGET_URL, headers=headers)
        res.raise_for_status()
        print(f"✅ アクセス成功 (Status: {res.status_code})")

        # HTML解析
        soup = BeautifulSoup(res.text, 'html.parser')

        # Next.jsのデータ埋め込みタグを探す
        script_tag = soup.find("script", id="__NEXT_DATA__")
        
        if not script_tag:
            print("❌ エラー: '__NEXT_DATA__' タグが見つかりませんでした。サイト構造が変わった可能性があります。")
            return

        print("✅ JSONデータ発見！解析します...")
        data = json.loads(script_tag.string)

        # --- データの掘り起こし ---
        # 構造を推測してイベントリストを探します
        try:
            # 一般的なNext.jsサイトの構造 (props -> pageProps -> initialState -> publicCalendar -> events)
            base_data = data.get('props', {}).get('pageProps', {})
            
            # デバッグ用にキーを表示
            # print(f"Debug Keys: {base_data.keys()}")
            
            initial_state = base_data.get('initialState', {})
            public_calendar = initial_state.get('publicCalendar', {})
            events = public_calendar.get('events', [])

            if not events:
                print("⚠️ イベントリストが空、またはパスが違います。")
                # 念のため raw data の一部を表示
                print(f"Top Level Keys: {data.keys()}")
                return

            print(f"🎉 取得成功！ {len(events)} 件のイベントが見つかりました。\n")
            print("--- 直近のイベント ---")

            for i, event in enumerate(events[:5]): # 最初の5件だけ表示
                title = event.get('title', 'No Title')
                start_at = event.get('start_at') # ミリ秒のタイムスタンプ
                
                # 日付変換
                if start_at:
                    dt = datetime.datetime.fromtimestamp(start_at / 1000)
                    date_str = dt.strftime('%Y/%m/%d %H:%M')
                else:
                    date_str = "日時不明"

                print(f"[{i+1}] {date_str} : {title}")

        except Exception as e:
            print(f"❌ JSON解析エラー: {e}")
            # 構造が変わっている場合のために、データの一部をダンプするなどの対応が必要

    except Exception as e:
        print(f"❌ 通信エラー: {e}")

if __name__ == "__main__":
    check_timetree()