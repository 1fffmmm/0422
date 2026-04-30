import os
import json
import time
import re
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    # ==========================================
    # 1. 自動日付計算 (JST固定)
    # ==========================================
    jst = timezone(timedelta(hours=9), 'JST')
    now = datetime.now(jst)
    tomorrow = now + timedelta(days=1)
    
    target_ym = tomorrow.strftime("%Y%m") 
    target_day = str(tomorrow.day)

    # ユーザー指定の直叩きURL形式に修正
    # list -> media_list に変更し、rw=3000 を追加
    url = f"https://jr-official.starto.jp/s/jr/media/media_list?dy={target_ym}&rw=3000"

    print(f"--- メディア監視システム起動 ---")
    print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"取得対象日: {tomorrow.strftime('%Y年%m月%d日')}")
    print(f"アクセスURL: {url}")

    # ==========================================
    # 2. ブラウザ設定
    # ==========================================
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=ja-JP')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:    
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 直接ターゲットのURLへ
        driver.get(url)

        print("コンテンツ読み込み中 (15秒待機)...")
        time.sleep(15) 

        # ページ全体のテキスト、または 'main' 要素を取得
        # media_list の場合は構造がシンプルになっている可能性があるため body も検討
        try:
            container = driver.find_element(By.TAG_NAME, 'main')
        except:
            container = driver.find_element(By.TAG_NAME, 'body')
            
        text_lines = container.text.splitlines()

        # デバッグ用：取得データの冒頭を表示
        print(f"--- 取得データプレビュー (最初の5行) ---")
        for i, line in enumerate(text_lines[:5]):
            print(f"{i+1}: {line}")
        print("---------------------------------------")

        # ==========================================
        # 3. 明日のスケジュール抽出ロジック
        # ==========================================
        # 日付形式 (例: "1", "1 (金)", "01") に対応
        date_pattern = re.compile(r"^(\d{1,2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        for line in text_lines:
            line = line.strip()
            if not line: continue
            
            match = date_pattern.match(line)
            if match:
                current_day_str = match.group(1) 
                # "01" などの 0 埋めを除去して比較
                if current_day_str.lstrip('0') == target_day.lstrip('0'):
                    recording = True
                    continue 
                else:
                    if recording: break 
            
            if recording:
                tomorrow_schedule.append(line)

        # ==========================================
        # 4. 取得結果の確定
        # ==========================================
        if tomorrow_schedule:
            content_text = "\n".join(tomorrow_schedule)
            print(f"【成功】 {target_day}日のデータを {len(tomorrow_schedule)} 件取得しました。")
        else:
            content_text = "明日の出演予定は見つかりませんでした。"
            print(content_text)

        return content_text 

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

    finally:
        if driver:
            driver.quit()
            print("ブラウザを閉じました。")

if __name__ == "__main__":
    main()
