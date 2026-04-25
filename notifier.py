import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

def check_keywords_and_notify(drive_text):
    print("--- 2. Firestore 照合処理開始 ---")
    
    # --- Firebase 初期化 ---
    if not firebase_admin._apps:
        # GitHub Secrets からJSON文字列を取得
        cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        if cred_json:
            # GitHub Actions環境（JSON文字列から認証）
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # ローカル開発環境（手元のファイルから認証）
            firebase_admin.initialize_app(credentials.Certificate("firebase-key.json"))

    db = firestore.client()

    try:
        # --- 1. Firestoreから全ユーザーのキーワードを取得 ---
        # コレクション名 'keywords' から全データを取得
        docs = db.collection('keywords').stream()
        
        all_keywords = []
        for doc in docs:
            data = doc.to_dict()
            if 'word' in data:
                all_keywords.append(data['word'])

        if not all_keywords:
            print("キーワードが登録されていません。")
            return

        # --- 2. Google Driveのテキストと照合 ---
        found_keywords = [word for word in all_keywords if word in drive_text]
        
        if found_keywords:
            print(f"【一致あり】: {found_keywords}")
            # ※ここに後ほど FCM (Firebase Cloud Messaging) の通知処理を追加します
        else:
            print("一致なし。")
            
    except Exception as e:
        print(f"Firestore ERROR: {e}")

if __name__ == "__main__":
    # テスト用（必要に応じて）
    check_keywords_and_notify("テスト用のテキストです")
    
