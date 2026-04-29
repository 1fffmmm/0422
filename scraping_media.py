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
from webdriver_manager.chrome import ChromeDriverManager
import firebase_admin
from firebase_admin import credentials, firestore
# --- 【修正1】インポートは一番上に追加します ---
from notifier import check_keywords_and_notify


# ==========================================
# 1. Firestoreの初期化設定
# ==========================================
def init_firestore():
    if not firebase_admin._apps:
        # GitHub Secrets に保存した JSON文字列（またはBase64）を取得
        cred_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
        if not cred_json:
            raise Exception("エラー: GCP_SERVICE_ACCOUNT_KEY が環境変数に設定されていません。")

        try:
            # JSONとして読み込み
            cred_dict = json.loads(cred_json)
        except json.JSONDecodeError:
            # JSONでない場合はBase64エンコードを疑ってデコード
            cred_dict = json.loads(base64.b64decode(cred_json).decode('utf-8'))
            
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def main():
    # Firestore クライアントの準備
    db = init_firestore()

    # ==========================================
    # 2. 自動日付計算
    # ==========================================
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    url_ym = tomorrow.strftime("%Y%m")
    target_day = tomorrow.strftime("%d")

    url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"

    print(f"--- メディア監視システム起動 ---")
    print(f"対象日: {tomorrow.strftime('%Y年%m月%d日')}")
    print(f"URL: {url}")

    # ==========================================
    # 3. ブラウザ設定 (GitHub Actions / Linux対応)
    # ==========================================
    options = Options()
    options.add_argument('--headless')          # 画面を表示しない
    options.add_argument('--no-sandbox')         # Linux環境での実行に必須
    options.add_argument('--disable-dev-shm-usage') # メモリ不足防止
    options.add_argument('--disable-gpu')
    # --- 【追加】日本語を優先的に取得するための設定 ---
    options.add_argument('--lang=ja-JP')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})
    # ----------------------------------------------
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:
        # WebDriverの自動セットアップ
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        print("サイト読み込み中 (15秒待機)...")
        time.sleep(15) # サイトの読み込みが遅いため長めに待機

        main_element = driver.find_element(By.TAG_NAME, 'main')
        text_lines = main_element.text.splitlines()

        # 再読み込み判定
        if "Loading" in main_element.text or len(text_lines) < 5:
             print("コンテンツが未ロードのため再待機します...")
             time.sleep(10)
             main_element = driver.find_element(By.TAG_NAME, 'main')
             text_lines = main_element.text.splitlines()

        # ==========================================
        # 4. 明日のスケジュール抽出ロジック
        # ==========================================
        date_pattern = re.compile(r"^(\d{2})(?:\s*\(.\))?$")
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
                else:
                    if recording: break # 次の日付に来たら終了
            
            if recording:
                tomorrow_schedule.append(line)

        # ==========================================
        # 5. Firestoreへの保存処理
        # ==========================================
        if tomorrow_schedule:
            # 抽出したリストを1つのテキストにまとめる
            content_text = "\n".join(tomorrow_schedule)
        else:
            content_text = "明日の出演予定は見つかりませんでした。"

        print("Firestoreへデータを保存しています...")
        
        # analysis_logs コレクションへドキュメントを追加
        doc_ref = db.collection('analysis_logs').document()
        doc_ref.set({
            "text": content_text,
            "source": "media",          # インスタ監視と区別するための識別子
            "updated_at": firestore.SERVER_TIMESTAMP,
            "target_date": tomorrow.strftime('%Y-%m-%d')
        })
        
        print(f"成功: Firestoreに保存完了 (ID: {doc_ref.id})")
        
# ==========================================
        # 【修正2】通知処理はこの位置（tryブロックの中）に追加します
        # ==========================================
        print("通知チェックを開始します...")
        check_keywords_and_notify(content_text, source="media")
        print("通知処理が完了しました。")
        

    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")
    
    finally:
        if driver:
            driver.quit()
            print("ブラウザを閉じました。")

if __name__ == "__main__":
    main()
