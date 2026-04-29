import os
import json
import datetime
from datetime import timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# ---------------------------------------------------------
# 1. Firebaseの初期化
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

# ---------------------------------------------------------
# 2. 古いデータの削除（クリーンアップ）
# ---------------------------------------------------------
def cleanup_expired_docs(db):
    """
    expire_at が現在時刻を過ぎているドキュメントを削除する
    """
    now = datetime.datetime.now(timezone.utc)
    collections = ["notification_history", "analysis_logs"]
    
    for coll_name in collections:
        try:
            # expire_at が現在時刻より古いものを検索
            old_docs = db.collection(coll_name).where("expire_at", "<", now).stream()
            deleted_count = 0
            for doc in old_docs:
                doc.reference.delete()
                deleted_count += 1
            
            if deleted_count > 0:
                print(f"🗑️ {coll_name}: 古いデータを {deleted_count} 件削除しました。")
        except Exception as e:
            print(f"{coll_name} クリーンアップエラー: {e}")

# ---------------------------------------------------------
# 3. メイン処理：キーワード照合と通知
# ---------------------------------------------------------
def check_keywords_and_notify(content_text, image_ids=None, source="insta"):
    if image_ids is None:
        image_ids = []
        
    db = firestore.client()
    now = datetime.datetime.now(timezone.utc)
    
    # 期限の設定
    expire_7days = now + timedelta(days=7)
    expire_2days = now + timedelta(days=2)

    print(f"--- ログ保存 & 通知処理開始 (ソース: {source}) ---")

    # --- ステップA: 全体ログの保存 (7日で自動削除対象) ---
    try:
        db.collection("analysis_logs").add({
            "content": content_text,
            "image_ids": image_ids, 
            "source": source,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "expire_at": expire_7days  # 7日間の期限
        })
    except Exception as e:
        print(f"解析ログ保存失敗: {e}")

    # --- ステップB: キーワードとユーザーの照合 ---
    keywords_ref = db.collection("keywords").stream()
    user_matches = {}
    for doc in keywords_ref:
        item = doc.to_dict()
        word = item.get('keyword')
        uid = item.get('userId') or item.get('user_id')
        
        if word and uid and word in content_text:
            if uid not in user_matches:
                user_matches[uid] = set()
            user_matches[uid].add(word)

    # --- ステップC: ユーザーごとに通知判定と送信 ---
    for uid, matched_words in user_matches.items():
        try:
            subs_query = db.collection("subscriptions").where("user_id", "==", uid).limit(1).stream()
            subs_docs = list(subs_query)
            if not subs_docs: continue
                
            sub_data = subs_docs[0].to_dict()
            if not sub_data.get(f"{source}_enabled", True):
                continue

            display_source = "【インスタ更新】" if source == "insta" else "【メディア出演】"
            keyword_str = ", ".join(matched_words)
            message_body = f"{display_source} キーワード「{keyword_str}」を検知しました"

            # 1. 個別通知履歴への保存 (2日で自動削除対象)
            db.collection("notification_history").add({
                "user_id": uid,
                "message": message_body,
                "source": source,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "expire_at": expire_2days  # 2日間の期限
            })

            # 2. プッシュ通知の送信
            token = sub_data.get("fcm_token")
            if token:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=f"{display_source} 監視アラート",
                        body=message_body
                    ),
                    token=token,
                )
                messaging.send(message)
                print(f"✅ ユーザー {uid} へ通知送信完了")

        except Exception as e:
            print(f"通知送信エラー (UID: {uid}): {e}")

    # --- ステップD: 古いデータのクリーンアップ実行 ---
    cleanup_expired_docs(db)
