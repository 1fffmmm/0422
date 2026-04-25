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
    """
    Firestoreのキーワードと照合し、一致したユーザーに通知を送る
    """
    print("--- 2. Firestore 照合 & 通知処理開始 ---")
    db = firestore.client()

    # 1. ログの保存 (最新の結果を上書き保存したい場合は setDoc、履歴を残すなら add)
    try:
        db.collection("analysis_logs").add({
            "content": drive_text,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        print("✅ Firestoreに最新ログを保存しました。")
    except Exception as log_err:
        print(f"❌ ログ保存失敗: {log_err}")

    # 2. キーワード一覧の取得
for doc in keywords_ref:
    item = doc.to_dict()
    word = item.get('keyword')
    uid = item.get('user_id')  # ★ userId から user_id に統一
    
        if word and uid and word in drive_text:
            if uid not in user_matches:
                user_matches[uid] = []
            user_matches[uid].append(word)

    print(f"ヒットしたユーザー数: {len(user_matches)}人")

    # 3. 通知送信処理 (複数端末/複数トークンに対応)
    for uid, matched_words in user_matches.items():
        try:
            # そのユーザーに紐付く全てのトークンを取得
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
                    print(f"🚀 通知送信完了: ユーザー {uid} (Token: {token[:10]}...)")
        except Exception as e:
            print(f"通知エラー (UID: {uid}): {e}")
            
