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

def main():
    # ==========================================
    # 1. 自動日付計算 (JST固定)
    # ==========================================
    jst = timezone(timedelta(hours=9), 'JST')
    now = datetime.now(jst)
    tomorrow = now + timedelta(days=1)
    
    target_ym = tomorrow.strftime("%Y%m") # 例: "202605"
    target_day = str(tomorrow.day)         # 例: "1"

    # 最初は基本URL（現在の月のページ）にアクセスする
    base_url = "https://jr-official.starto.jp/s/jr/media/list"

    print(f"--- メディア監視システム起動 ---")
    print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"取得対象日: {tomorrow.strftime('%Y年%m月%d日')}")

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
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"基本URLにアクセス: {base_url}")
        driver.get(base_url)
        time.sleep(15) 

        # ==========================================
        # [重要] 月末時の翌月遷移ロジック
        # ==========================================
        # 明日が1日、かつ現在の画面がまだ前月(現在月)の場合
        if tomorrow.day == 1:
            print(f"【月末判定】翌月({target_ym})のボタンを探します...")
            try:
                # リンク内に "dy=202605" のような文字列が含まれるaタグを探す
                # 遷移ボタンが <a> タグである前提のセレクタです
                next_link_xpath = f"//a[contains(@href, 'dy={target_ym}')]"
                next_button = driver.find_element(By.XPATH, next_link_xpath)
                
                print("翌月ボタンを発見。クリックして遷移します。")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(10) # 遷移後の読み込み待機
            except Exception:
                # 指定した月のリンクがない場合（サイト側が未公開の場合）
                print(f"通知: サイト上に翌月({target_ym})のリンクが見つかりません。")
                print("まだ翌月のスケジュールが公開されていない可能性があります。")

        # コンテンツの取得
        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        # ロード待ち判定
        if "Loading" in main_element.text or len(text_lines) < 5:
             print("再ロード待機中...")
             time.sleep(10)
             main_element = driver.find_element(By.TAG_NAME, 'main')
             text_lines = main_element.text.splitlines()

        # ==========================================
        # 3. スケジュール抽出ロジック
        # ==========================================
        date_pattern = re.compile(r"^(\d{1,2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        for line in text_lines:
            line = line.strip()
            if not line: continue
            
            match = date_pattern.match(line)
            if match:
                current_day_str = match.group(1) 
                if current_day_str == target_day:
                    recording = True
                    continue 
                else:
                    if recording: break 
            
            if recording:
                tomorrow_schedule.append(line)

        # ==========================================
        # 4. 結果判定
        # ==========================================
        if tomorrow_schedule:
            content_text = "\n".join(tomorrow_schedule)
            print(f"データ取得成功: {len(tomorrow_schedule)}件の情報を抽出しました。")
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
    
