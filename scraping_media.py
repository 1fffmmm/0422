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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    # 常に「今月のリスト」からスタートする
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
    # リアルなブラウザに見せかけるためのUser-Agent設定
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:    
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"サイトにアクセス中: {base_url}")
        driver.get(base_url)

        # 画面が読み込まれるのを待つ
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))

        # ==========================================
        # [改良] 月末時の翌月遷移ロジック
        # ==========================================
        if tomorrow.day == 1:
            print("【月末判定】翌月ボタンを検索中...")
            try:
                # 複数の方法で「翌月ボタン」を探索
                # 1. クラス名に 'next' を含む a タグ
                # 2. href に dy=202605 を含む a タグ
                # 3. テキストに '次月' や '＞' を含む要素
                next_selectors = [
                    f"//a[contains(@href, 'dy={target_ym}')]",
                    "//li[contains(@class, 'next')]/a",
                    "//a[contains(@class, 'next')]",
                    "//span[contains(text(), '次月')]/.."
                ]
                
                next_button = None
                for selector in next_selectors:
                    try:
                        next_button = driver.find_element(By.XPATH, selector)
                        if next_button: break
                    except:
                        continue

                if next_button:
                    print(f"翌月ボタンを発見しました。クリックします。")
                    # 画面外にある場合を考慮してスクロール
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button)
                    
                    print("遷移完了を待機中 (10秒)...")
                    time.sleep(10)
                else:
                    print("翌月ボタンが見つかりませんでした。URLの直接指定を試みます。")
                    driver.get(f"{base_url}?dy={target_ym}")
                    time.sleep(10)

            except Exception as e:
                print(f"ボタン操作中にエラーが発生しました。続行します: {e}")

        # コンテンツの抽出
        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        # ==========================================
        # 3. スケジュール抽出ロジック
        # ==========================================
        date_pattern = re.compile(r"^(\d{1,2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        print(f"デバッグ: 取得したテキストの最初の5行:\n{text_lines[:5]}")

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
        # 4. 結果確定
        # ==========================================
        if tomorrow_schedule:
            content_text = "\n".join(tomorrow_schedule)
            print(f"データ取得成功: {target_day}日の予定を {len(tomorrow_schedule)} 行取得しました。")
        else:
            content_text = "明日の出演予定は見つかりませんでした。"
            print(content_text)

        return content_text 

    except Exception as e:
        print(f"致命的なエラー: {e}")
        return None

    finally:
        if driver:
            driver.quit()
            print("ブラウザを閉じました。")

if __name__ == "__main__":
    main()
