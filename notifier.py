import os
import json
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

def check_keywords_and_notify(drive_text):
    print("--- 2. Firestore 照合 & 通知処理開始 ---")
    db = firestore.client()

    try:
        db.collection("analysis_logs").add({
            "content": drive_text,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        print("✅ Firestoreに最新ログを保存しました。")
    except Exception as log_err:
        print(f"❌ ログ保存失敗: {log_err}")

    keywords_ref = db.collection("keywords").stream()
    
    user_matches = {}
    for doc in keywords_ref:
        item = doc.to_dict()
        word = item.get('keyword')
        # ★ Firestoreのフィールド名が userId なら 'userId'、user_id なら 'user_id' に合わせてください
        uid = item.get('userId') or item.get('user_id')
        
        if word and uid and word in drive_text:
            if uid not in user_matches:
                user_matches[uid] = []
            user_matches[uid].append(word)

    print(f"ヒットしたユーザー数: {len(user_matches)}人")

    for uid, matched_words in user_matches.items():
        try:
            subs_ref = db.collection("subscriptions").where("user_id", "==", uid).stream()
            for sub_doc in subs_ref:
                token = sub_doc.to_dict().get("fcm_token")
                if token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="監視アラート",
                            body=f"キーワード「{', '.join(matched_words)}」を検知しました"
                        ),
                        token=token,
                    )
                    messaging.send(message)
                    print(f"🚀 通知送信完了: ユーザー {uid}")
        except Exception as e:
            print(f"通知エラー (UID: {uid}): {e}")
            
