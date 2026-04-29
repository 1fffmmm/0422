import os
import json
import time
import re
import base64
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. Firestoreの初期化
# ==========================================
def init_firestore():
    if not firebase_admin._apps:
        cred_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        if not cred_json:
            raise Exception("エラー: GCP_SERVICE_ACCOUNT_KEY が設定されていません。")

        try:
            # そのままJSONとして試行
            cred_dict = json.loads(cred_json)
        except json.JSONDecodeError:
            # 失敗した場合はBase64としてデコード
            cred_dict = json.loads(base64.b64decode(cred_json).decode('utf-8'))
            
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def main():
    # --- 日付計算 ---
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    url_ym = tomorrow.strftime("%Y%m")
    target_day = tomorrow.strftime("%d")

    url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"

    print(f"--- メディア監視システム起動 ---")
    print(f"対象日: {tomorrow.strftime('%Y年%m月%d日')} / URL: {url}")

    # --- ブラウザ設定 ---
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:    
        db = init_firestore()
        # 最新のSeleniumでは Service() のみでドライバーは自動管理されます
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # 明示的待機: <main>タグが現れるまで最大20秒待つ
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'main')))
        
        # 動的コンテンツの読み込みを少しだけ待つ
        time.sleep(5)

        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        # --- 抽出ロジック ---
        # 日付パターン: "30" や "30 (月)" にマッチ
        date_pattern = re.compile(r"^(\d{1,2})(?:\s*\(.\))?$")
        recording = False
        tomorrow_schedule = []

        for line in text_lines:
            line = line.strip()
            if not line: continue
            
            match = date_pattern.match(line)
            if match:
                current_day_str = match.group(1).zfill(2) # "1" を "01" に変換して比較
                if current_day_str == target_day:
                    recording = True
                    continue # 日付行自体はリストに入れない
                elif recording:
                    break # 次の日付が来たら終了
            
            if recording:
                tomorrow_schedule.append(line)

        # --- 保存処理 ---
        content_text = "\n".join(tomorrow_schedule) if tomorrow_schedule else "明日の出演予定は見つかりませんでした。"

        print("Firestoreへ保存中...")
        doc_ref = db.collection('analysis_logs').document()
        doc_ref.set({
            "text": content_text,
            "source": "media",
            "updated_at": firestore.SERVER_TIMESTAMP,
            "target_date": tomorrow.strftime('%Y-%m-%d')
        })
        
        print(f"成功: ID {doc_ref.id}")
        return content_text 

    except Exception as e:
        print(f"エラー発生: {e}")
    finally:
        if driver:
            driver.quit()
            print("ブラウザを終了しました。")

if __name__ == "__main__":
    main()
