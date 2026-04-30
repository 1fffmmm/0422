import os
import json
import time
import re
import base64
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ※ Firestoreの初期化は notifier.py 側で行うため、ここでは不要になりますが、
# もし単体で動かすテストをしたい場合は残しておいてもOKです。
# 今回は notifier.py に任せる前提で書き換えを最小限にします。

def main():
    # ==========================================
    # 1. 自動日付計算 (JST固定)
    # ==========================================
    # これでサーバーがどこにあっても日本時間で計算されます
    jst = timezone(timedelta(hours=9), 'JST')
    now = datetime.now(jst)
    tomorrow = now + timedelta(days=1)
    
    url_ym = tomorrow.strftime("%Y%m")
    # target_day は 比較しやすいように "1", "2" 形式（zfillなし）にするのが確実です
    target_day = str(tomorrow.day) 

    url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"

    print(f"--- メディア監視システム起動 ---")
    print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象日: {tomorrow.strftime('%Y年%m月%d日')}")
    print(f"URL: {url}")
    

    # ==========================================
    # 2. ブラウザ設定
    # ==========================================
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:    
        # WebDriverのセットアップ
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        print("サイト読み込み中 (15秒待機)...")
        time.sleep(15) 

        # ==========================================
        # [追加] 月末時の翌月カレンダークリック処理
        # ==========================================
        if tomorrow.day == 1:
            print("【月末判定】明日が1日のため、ブラウザ上で翌月への切り替えを試行します...")
            try:
                # 対象の年月（dy=YYYYMM）をリンクに含む要素を探す
                target_xpath = f"//a[contains(@href, 'dy={url_ym}')]"
                next_button = driver.find_element(By.XPATH, target_xpath)
                
                # 通常のclick()ではなく、JS経由でクリック（ヘッドレス環境での安定性向上のため）
                driver.execute_script("arguments[0].click();", next_button)
                print(f"翌月({url_ym})へのリンクをクリックしました。再読み込みを待機します (10秒)...")
                time.sleep(10)
            except Exception as e:
                print(f"翌月へのリンクが見つからないか、クリックできませんでした。そのまま続行します。詳細: {e}")

        # 要素の取得
        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        # 再読み込み判定
        if "Loading" in main_element.text or len(text_lines) < 5:
             print("コンテンツが未ロードのため再待機します...")
             time.sleep(10)
             main_element = driver.find_element(By.TAG_NAME, 'main')
             text_lines = main_element.text.splitlines()

        # ==========================================
        # 3. 明日のスケジュール抽出ロジック
        # ==========================================
        date_pattern = re.compile(r"^(\d{1,2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        for line in text_lines:
            line = line.strip()
            if not line: continue
            
            match = date_pattern.match(line)
            if match:
                # 取得した日付も zfill せずに比較
                current_day_str = match.group(1) 
                if current_day_str == target_day:
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
        else:
            content_text = "明日の出演予定は見つかりませんでした。"

        # 【削除】Firestoreへの保存処理(db.collection...set)をここから消しました。
        # 保存は main.py から呼ばれる notifier.py 側で自動的に行われます。
        
        print(f"データ取得成功。")
        return content_text 

    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")
        return None

    finally:
        if driver:
            driver.quit()
            print("ブラウザを閉じました。")

if __name__ == "__main__":
    main()
