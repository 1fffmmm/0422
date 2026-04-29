import os
import json
import datetime
from datetime import timedelta
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

# ---------------------------------------------------------
# メイン処理：キーワードチェックと通知
# ---------------------------------------------------------
def check_keywords_and_notify(content_text, image_ids=None, source="insta"):
    """
    content_text: 取得したテキスト
    image_ids: 画像IDリスト
    source: "insta" または "media"
    """
    if image_ids is None:
        image_ids = []
        
    db = firestore.client()
    now = datetime.datetime.now(datetime.timezone.utc)
    # 2日後の時間を計算（FirestoreのTTL機能用）
    ttl_expiry = now + timedelta(days=2)

    print(f"--- 通知処理開始 (ソース: {source}) ---")

    # 1. 解析ログの保存（生データの記録：Web画面のメイン表示用）
    # ※ここは削除せず、最新の情報を表示するために残します
    try:
        db.collection("analysis_logs").add({
            "content": content_text,
            "image_ids": image_ids, 
            "source": source,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"解析ログ保存失敗: {e}")

    # 2. キーワード情報の取得
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

    # 3. ユーザーごとに通知を判定して送信
    for uid, matched_words in user_matches.items():
        try:
            # 購読情報の取得（重複がない前提で最新の1件を取得）
            subs_query = db.collection("subscriptions").where("user_id", "==", uid).limit(1).stream()
            subs_docs = list(subs_query)
            
            if not subs_docs:
                print(f"ユーザー {uid} の購読情報が見つからないためスキップします。")
                continue
                
            sub_data = subs_docs[0].to_dict()
            
            # 通知の出し分け判定 (insta_enabled / media_enabled)
            is_enabled = sub_data.get(f"{source}_enabled", True)
            if not is_enabled:
                print(f"ユーザー {uid} は {source} 通知をオフにしているためスキップします。")
                continue

            # 通知本文の作成
            display_source = "【インスタ更新】" if source == "insta" else "【メディア出演】"
            keyword_str = ", ".join(matched_words)
            message_body = f"{display_source} キーワード「{keyword_str}」を検知しました"

            # 4. 通知履歴（notification_history）への保存
            # ここに「expire_at」を入れることで、Firestoreが自動で2日後に消してくれます
            db.collection("notification_history").add({
                "user_id": uid,
                "message": message_body,
                "source": source,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "expire_at": ttl_expiry  # これが重要！
            })

            # 5. プッシュ通知送信
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
                print(f"✅ ユーザー {uid} に {source} 通知を送信しました。")

        except Exception as e:
            print(f"通知送信エラー (UID: {uid}): {e}")

    # 手動削除関数は、TTL設定を行う場合は呼び出さなくてOKです
    # delete_old_logs(db)
