import os
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# ---------------------------------------------------------
# Firebaseの初期化 (既存のまま)
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

def delete_old_logs(db):
    print("--- 3. 古いログの自動削除処理を開始 ---")
    try:
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        docs = db.collection("analysis_logs").where("updated_at", "<", cutoff_date).limit(50).stream()
        
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
            
        if deleted_count > 0:
            print(f"🧹 {deleted_count}件の古いログを削除しました。")
        else:
            print("✨ 削除対象の古いログはありませんでした。")
    except Exception as e:
        print(f"❌ 古いログの削除中にエラーが発生しました: {e}")

# ---------------------------------------------------------
# メイン処理：キーワード照合 & 通知 & タグ付け保存
# ---------------------------------------------------------
def check_keywords_and_notify(drive_text, image_ids=None):
    if image_ids is None:
        image_ids = []
        
    print("--- 2. Firestore 照合 & 通知処理開始 (Instagram版) ---")
    db = firestore.client()

    # 1. 取得した全テキストのログ保存 (source: "insta" を追加)
    try:
        db.collection("analysis_logs").add({
            "content": drive_text,
            "image_ids": image_ids, 
            "source": "insta",          # ★ここを追加：インスタ由来であることを明示
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        print("✅ Firestoreにインスタログと画像IDを保存しました。")
    except Exception as log_err:
        print(f"❌ ログ保存失敗: {log_err}")

    # キーワード取得と照合ロジック (既存のまま)
    keywords_ref = db.collection("keywords").stream()
    user_matches = {}
    for doc in keywords_ref:
        item = doc.to_dict()
        word = item.get('keyword')
        uid = item.get('userId') or item.get('user_id')
        
        if word and uid and word in drive_text:
            if uid not in user_matches:
                user_matches[uid] = []
            user_matches[uid].append(word)

    print(f"ヒットしたユーザー数: {len(user_matches)}人")

    # 通知送信ループ
    for uid, matched_words in user_matches.items():
        try:
            keyword_str = ", ".join(matched_words)
            message_body = f"【インスタ】キーワード「{keyword_str}」を検知しました"

            # 2. ユーザーごとの通知ログ保存 (ここにも source: "insta" を追加)
            db.collection("analysis_logs").add({
                "user_id": uid,
                "message": message_body,
                "matched_keywords": list(matched_words),
                "source": "insta",      # ★ここを追加：通知履歴も判別可能にする
                "updated_at": firestore.SERVER_TIMESTAMP
            })

            # 実際のプッシュ通知送信 (既存のまま)
            subs_ref = db.collection("subscriptions").where("user_id", "==", uid).stream()
            for sub_doc in subs_ref:
                token = sub_doc.to_dict().get("fcm_token")
                if token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="インスタ更新アラート",
                            body=message_body
                        ),
                        token=token,
                    )
                    messaging.send(message)
            
            print(f"✅ ユーザー {uid} に通知を送信しました。")

        except Exception as e:
            print(f"通知処理エラー (UID: {uid}): {e}")
            
    # 古いログの削除
    delete_old_logs(db)
    
