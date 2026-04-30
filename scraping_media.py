import time
import re
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def main():
    # 1. 日本時間での計算
    jst = timezone(timedelta(hours=9), 'JST')
    now = datetime.now(jst)
    tomorrow = now + timedelta(days=1)
    
    target_ym = tomorrow.strftime("%Y%m") # 例: 202605
    target_day = str(tomorrow.day)         # 例: 1

    base_url = "https://jr-official.starto.jp/s/jr/media/list"

    print(f"--- メディア監視システム起動 ---")
    print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # 2. ブラウザ設定（GitHub Actions最適化）
    options = Options()
    options.add_argument('--headless') # GitHubでは必須
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080') # 画面サイズを固定
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:    
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"基本URLにアクセス中: {base_url}")
        driver.get(base_url)
        
        # 読み込み待機
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        time.sleep(5) 

        # 3. 月末限定：翌月への強制遷移
        if tomorrow.day == 1:
            print(f"【月末判定】翌月({target_ym})への遷移を開始...")
            
            # Full XPathが環境によって変わるのを防ぐため、複数の指定方法を試す
            # span[2] という指定よりも、クラス名を組み合わせるのが安全です
            xpath_candidates = [
                "//div[contains(@class, 'p-media__header')]//span[2]", 
                "/html/body/div[1]/main/div[1]/div/div[3]/section/div/div[1]/div/div[2]/span[2]",
                "//div[contains(@class, 'p-media__header')]//img/.."
            ]

            success = False
            for path in xpath_candidates:
                try:
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, path)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", element)
                    print(f"成功: 要素をクリックしました (Path: {path})")
                    success = True
                    break 
                except:
                    continue

            if success:
                time.sleep(15) # 遷移待機
                print(f"現在のURL: {driver.current_url}")
            else:
                print("致命的エラー: 翌月ボタンを特定できませんでした。")

        # 4. テキスト抽出
        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        date_pattern = re.compile(r"^(\d{1,2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        for line in text_lines:
            line = line.strip()
            if not line: continue
            match = date_pattern.match(line)
            if match:
                if match.group(1).lstrip('0') == target_day:
                    recording = True
                    continue
                elif recording:
                    break
            if recording:
                tomorrow_schedule.append(line)

        if tomorrow_schedule:
            result = "\n".join(tomorrow_schedule)
            print(f"【成功】 {target_day}日のデータを取得しました。")
            return result
        else:
            print("明日の出演予定は見つかりませんでした。")
            return "予定なし"

    except Exception as e:
        print(f"エラー発生: {e}")
    finally:
        if driver:
            driver.quit()
            print("ブラウザを終了しました。")

if __name__ == "__main__":
    main()
