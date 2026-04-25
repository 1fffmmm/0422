import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# ---------------------------------------------------------
# Firebaseの初期化
# ---------------------------------------------------------
if not firebase_admin._apps:
    service_account_info_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_info_str:
        try:
            cred_dict = json.loads(service_account_info_str)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Firebase初期化エラー: {e}")
    else:
        print("エラー: FIREBASE_SERVICE_ACCOUNT_JSONが設定されていません。")

# ---------------------------------------------------------
# 1. Google Driveからテキスト取得
# ---------------------------------------------------------
def get_drive_text():
    print("--- 1. Google Drive 処理開始 ---")
    file_id = os.environ.get("DRIVE_FILE_ID")
    gcp_key_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    
    if not gcp_key_str or not file_id:
        print(f"エラー: 環境変数が不足しています (FILE_ID: {file_id})")
        return None

    try:
        # evalは危険なため json.loads を推奨
        service_account_info = json.loads(gcp_key_str)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        service = build('drive', 'v3', credentials=creds)

        print(f"Google Drive(ID: {file_id}) からダウンロード中...")
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        drive_text = fh.getvalue().decode('utf-8')
        print(f"読み込み成功: {len(drive_text)}文字取得しました。")
        return drive_text
    except Exception as e:
        print(f"Driveダウンロードエラー: {e}")
        return None

# ---------------------------------------------------------
# 2. Firestore照合と通知送信
# ---------------------------------------------------------
def check_keywords_and_notify(drive_text):
    print("--- 2. Firestore 照合 & 通知処理開始 ---")
    db = firestore.client()

    # ログの保存 (main.htmlに合わせて updated_at に修正)
    try:
        db.collection("analysis_logs").add({
            "content": drive_text,
            "updated_at": firestore.SERVER_TIMESTAMP  # ★修正: created_at から変更
        })
        print("✅ Firestoreに最新ログを保存しました。")
    except Exception as log_err:
        print(f"❌ ログ保存失敗: {log_err}")

    # キーワード取得
    keywords_ref = db.collection("keywords").stream()
    
    user_matches = {}
    count = 0
    for doc in keywords_ref:
        item = doc.to_dict()
        count += 1
        # ★修正: main.html側の保存名 (keyword / userId) に合わせる
        word = item.get('keyword')
        uid = item.get('userId')
        
        if word and uid and word in drive_text:
            if uid not in user_matches:
                user_matches[uid] = []
            user_matches[uid].append(word)

    print(f"登録キーワード数: {count}個 / ヒットしたユーザー: {len(user_matches)}人")

    # 通知送信
    for uid, matched_words in user_matches.items():
        try:
            # main.htmlで保存している user_id フィールドを検索
            subs_ref = db.collection("subscriptions").where("user_id", "==", uid).stream()
            
            for sub_doc in subs_ref:
                token = sub_doc.to_dict().get("fcm_token")
                if token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="監視アラート",
                            body=f"キーワード「{', '.join(matched_words)}」を検知"
                        ),
                        token=token,
                    )
                    messaging.send(message)
                    print(f"🚀 通知送信完了: ユーザー {uid}")
        except Exception as e:
            print(f"通知エラー (UID: {uid}): {e}")

if __name__ == "__main__":
    print("=== プログラム実行開始 ===")
    text = get_drive_text()
    if text is not None: # 空文字でも保存処理に回す
        check_keywords_and_notify(text)
    else:
        print("エラー: テキストが取得できなかったため、Firestore処理をスキップしました。")
    print("=== 全処理終了 ===")
