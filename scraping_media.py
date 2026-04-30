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
    jst = timezone(timedelta(hours=9), 'JST')
    now = datetime.now(jst)
    tomorrow = now + timedelta(days=1)
    
    target_ym = tomorrow.strftime("%Y%m") # 202605
    target_day = str(tomorrow.day)         # 1

    # 1. まずは基本のリストページへ
    base_url = "https://jr-official.starto.jp/s/jr/media/list"

    print(f"--- メディア監視システム起動 ---")
    print(f"現在時刻 (JST): {now.strftime('%Y-%m-%d %H:%M:%S')}")

    options = Options()
# options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:    
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # ステップ1: 基本URLにアクセス
        print(f"基本URLにアクセス中: {base_url}")
        driver.get(base_url)
        
        # ステップ2: ページ読み込み完了を待機（URLに現在の月が含まれるまで待つ）
        wait = WebDriverWait(driver, 20)
        wait.until(lambda d: "dy=" in d.current_url or d.find_element(By.TAG_NAME, "main"))
        print(f"初期ロード完了: {driver.current_url}")
        time.sleep(5) # スクリプト実行の安定のため少し待機

        # ==========================================
        # Step 3: [月末限定] 翌月への強制遷移ロジック
        # ==========================================
        if tomorrow.day == 1:
            print(f"【月末判定】翌月({target_ym})への遷移を開始します...")
            
            # ページが安定するまで少し待機
            time.sleep(5)

            # ユーザーが取得したピンポイントな住所（Full XPath）
            # span[2]（外枠）と img（画像）の両方を候補に入れます
            xpath_candidates = [
                "/html/body/div[1]/main/div[1]/div/div[3]/section/div/div[1]/div/div[2]/span[2]",
                "/html/body/div[1]/main/div[1]/div/div[3]/section/div/div[1]/div/div[2]/span[2]/img"
            ]

            success = False
            for path in xpath_candidates:
                try:
                    # 要素が見つかり、クリック可能になるまで待機
                    element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, path))
                    )
                    
                    # 1. 念のためその場所までスクロール
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # 2. JavaScriptで直接クリックイベントを発生させる
                    driver.execute_script("arguments[0].click();", element)
                    
                    print(f"成功: 要素をクリックしました (XPath: {path})")
                    success = True
                    break # 成功したらループを抜ける
                except Exception as e:
                    print(f"試行失敗: {path} は見つからないかクリックできませんでした。")
                    continue

            if success:
                print("遷移後の読み込みを待機中 (15秒)...")
                time.sleep(15)
                # 本当にURLや中身が変わったか確認
                print(f"現在のURL: {driver.current_url}")
            else:
                print("致命的エラー: 翌月ボタンを特定できませんでした。")

        # --- 以降、テキスト抽出ロジックへ ---
        


        # ステップ4: テキスト抽出
        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        # スケジュール抽出（前回のロジックを流用）
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
            print(f"【成功】 {target_day}日のデータを取得しました。")
            return "\n".join(tomorrow_schedule)
        else:
            print("明日の出演予定は見つかりませんでした。")
            return "予定なし"

    except Exception as e:
        print(f"エラー: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
