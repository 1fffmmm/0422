import time
import re
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_media_schedule():
    """
    メディアサイトから明日のスケジュールを取得し、テキストとして返す関数
    """
    # 1. 日本時間（JST）での自動日付計算
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(JST)
    tomorrow = now + timedelta(days=1)

    url_ym = tomorrow.strftime("%Y%m")
    target_day = tomorrow.strftime("%d")

    url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"
    print(f"明日の日付 ({tomorrow.strftime('%Y年%m月%d日')}) の情報を取得します...")

    # 2. GitHub Actions（Linuxサーバー）で動かすためのブラウザ設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')             # Linux環境必須
    options.add_argument('--disable-dev-shm-usage')  # メモリ不足対策
    options.add_argument('--window-size=1920,1080')  # 画面サイズ固定

    schedule_text = ""

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(10)

        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        if "Loading" in main_element.text or len(text_lines) < 10:
             print("まだ読み込み中のようです。さらに5秒待ちます...")
             time.sleep(5)
             main_element = driver.find_element(By.TAG_NAME, 'main')
             text_lines = main_element.text.splitlines()

        # 3. 明日のスケジュールだけを切り取る処理
        date_pattern = re.compile(r"^(\d{2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        for line in text_lines:
            line = line.strip()
            if not line:
                continue
            
            match = date_pattern.match(line)
            if match:
                current_day_str = match.group(1)
                if current_day_str == target_day:
                    recording = True
                else:
                    if recording:
                        break
            
            if recording:
                tomorrow_schedule.append(line)

        # 抽出したリストを改行で繋いで、ひとつの文字列にする
        if tomorrow_schedule:
            schedule_text = "\n".join(tomorrow_schedule)
        else:
            schedule_text = "明日の出演予定は見つかりませんでした。"
            
        print("抽出完了！")
        return schedule_text

    except Exception as e:
        print(f"スクレイピングエラー: {e}")
        return ""
    
    finally:
        try:
            driver.quit()
        except:
            pass

# 単体テスト用（このファイルだけを実行した時の動き）
if __name__ == "__main__":
    result = get_media_schedule()
    print("=== 取得結果 ===")
    print(result)
  
