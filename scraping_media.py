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

        # ステップ3: 明日が1日の場合のみ「＞」ボタンを探してクリック
        if tomorrow.day == 1:
            print("【月末判定】翌月ボタンを探してクリックします...")
            try:
                # 「＞」ボタンの特定（hrefに次の月が含まれているか、特定のクラスを持つもの）
                # サイトの構造に合わせ、複数の候補からボタンを探します
                selectors = [
                    f"//a[contains(@href, 'dy={target_ym}')]", # hrefに202605を含むaタグ
                    "//a[contains(@class, 'next')]",           # classにnextを含む
                    "//span[contains(text(), '次月')]/..",      # 「次月」という文字の親要素
                    "//a[text()='>']"                          # 単純な「>」テキスト
                ]
                
                next_button = None
                for s in selectors:
                    try:
                        next_button = driver.find_element(By.XPATH, s)
                        if next_button: break
                    except:
                        continue
                
                if next_button:
                    # JavaScriptでクリックを実行
                    driver.execute_script("arguments[0].click();", next_button)
                    print("翌月ボタンをクリックしました。遷移を待ちます...")
                    time.sleep(10)
                else:
                    print("翌月ボタンが見つかりませんでした。")
            except Exception as e:
                print(f"クリック処理中にエラー: {e}")

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
