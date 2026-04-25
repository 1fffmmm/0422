import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# ---------------------------------------------------------
# Firebaseの初期化（プログラム起動時に1回だけ実行）
# ---------------------------------------------------------
if not firebase_admin._apps:
    # GitHub Secretsに保存したFirebaseのサービスアカウントJSONを取得
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
    
    # Drive APIの認証 (既存の仕組みを維持)
    gcp_key_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not gcp_key_str:
        print("エラー: GCP_SERVICE_ACCOUNT_KEYが設定されていません。")
        return None

    # eval() または json.loads() で辞書形式に変換
    try:
        service_account_info = eval(gcp_key_str) 
    except:
        service_account_info = json.loads(gcp_key_str)

    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('drive', 'v3', credentials=creds)

    print("Google Driveからファイルをダウンロード中...")
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        drive_text = fh.getvalue().decode('utf-8')
        print(f"Google Driveからの読み込み成功（文字数: {len(drive_text)}文字）")
        return drive_text
    except Exception as e:
        print(f"Driveダウンロードエラー: {e}")
        return None

# ---------------------------------------------------------
# 2. Firestore照合と通知送信
# ---------------------------------------------------------
def check_keywords_and_notify(drive_text):
    print("--- 2. Firestore 照合 & FCM 通知処理開始 ---")
    db = firestore.client()

    # ログの保存
    try:
        db.collection("analysis_logs").add({
            "content": drive_text,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print("最新ログをFirestoreに保存しました。")
    except Exception as log_err:
        print(f"ログ保存エラー（続行します）: {log_err}")

    # Firestoreから全キーワードを取得
    keywords_ref = db.collection("keywords").stream()
    keywords_data = [doc.to_dict() for doc in keywords_ref]

    if not keywords_data:
        print("キーワードが登録されていません。")
        return

    # マッチング処理
    user_matches = {}
    for item in keywords_data:
        word = item.get('word')
        user_id = item.get('user_id')
        if word and user_id and word in drive_text:
            if user_id not in user_matches:
                user_matches[user_id] = []
            user_matches[user_id].append(word)

    if not user_matches:
        print("どのユーザーのキーワードとも一致しませんでした。")
        return

    print(f"【一致したユーザー数】: {len(user_matches)}人")

    # ユーザーごとに通知を送信
    for user_id, matched_words in user_matches.items():
        try:
            # 該当ユーザーのプッシュ通知トークンを取得
            subs_ref = db.collection("subscriptions").where("user_id", "==", user_id).stream()
            
            send_count = 0
            for sub_doc in subs_ref:
                token = sub_doc.to_dict().get("fcm_token")
                if not token:
                    continue
                
                # FCM通知メッセージの組み立て
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="監視アラート",
                        body=f"登録キーワード「{', '.join(matched_words)}」が見つかりました。"
                    ),
                    token=token,
                )
                
                # 送信実行
                response = messaging.send(message)
                send_count += 1
            
            if send_count > 0:
                print(f"通知送信成功: ユーザー {user_id} ({send_count}個のデバイス)")
            else:
                print(f"通知対象のトークンが見つかりませんでした: ユーザー {user_id}")

        except Exception as e:
            print(f"通知処理中の予期せぬエラー: ユーザー {user_id}, エラー: {e}")
            
    print("--- 3. 全ての処理が終了しました ---")

if __name__ == "__main__":
    print("プログラムを起動しました。")
    text = get_drive_text()
    if text:
        check_keywords_and_notify(text)
