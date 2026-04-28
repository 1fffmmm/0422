import os
import json
import datetime  # ★変更箇所1：日付計算のためのライブラリを追加
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

# ★変更箇所2：古いログを削除する専用の関数を新しく追加
def delete_old_logs(db):
    print("--- 3. 古いログの自動削除処理を開始 ---")
    try:
        # 7日前の日時を計算（UTC）
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        
        # 実際のコードに合わせて 'updated_at' を指定。7日より古いものを最大50件取得
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

# ★変更箇所3：引数に「image_ids」を追加し、Firestoreへの保存処理にも含める
def check_keywords_and_notify(drive_text, image_ids=None):
    if image_ids is None:
        image_ids = []
        
    print("--- 2. Firestore 照合 & 通知処理開始 ---")
    db = firestore.client()

    try:
        # ★保存するデータに "image_ids" の行を追加
        db.collection("analysis_logs").add({
            "content": drive_text,
            "image_ids": image_ids, 
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        print("✅ Firestoreに最新ログと画像IDを保存しました。")
    except Exception as log_err:
        print(f"❌ ログ保存失敗: {log_err}")

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

    
    # --- notifier.py の通知送信ループ部分 ---
    for uid, matched_words in user_matches.items():
        try:
            # 通知本文の作成
            keyword_str = ", ".join(matched_words)
            message_body = f"キーワード「{keyword_str}」を検知しました"

            # 1. Firestoreに「お知らせ」として保存（Web表示用）
            db.collection("analysis_logs").add({
                "user_id": uid,
                "message": message_body,  # ★このフィールドをWeb側で読み取る
                "matched_keywords": list(matched_words),
                "updated_at": firestore.SERVER_TIMESTAMP
            })

            # 2. 実際のプッシュ通知送信
            subs_ref = db.collection("subscriptions").where("user_id", "==", uid).stream()
            for sub_doc in subs_ref:
                token = sub_doc.to_dict().get("fcm_token")
                if token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title="監視アラート",
                            body=message_body
                        ),
                        token=token,
                    )
                    messaging.send(message)
            
            print(f"✅ ユーザー {uid} にお知らせを保存し、通知を送信しました。")

        except Exception as e:
            print(f"通知処理エラー (UID: {uid}): {e}")
            
            
    # ★変更箇所4：一番最後に、作成した「古いログの削除関数」を呼び出す
    delete_old_logs(db)
    
