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
# 2. 定数・設定
# ---------------------------------------------------------
# ソースごとの表示名と設定キーの定義
SOURCE_CONFIG = {
    "insta": {"label": "【ストーリー】", "title": "インスタ更新"},
    "media": {"label": "【出演情報】", "title": "メディア出演情報"},
    "tweet": {"label": "【ツイート】", "title": "ツイート更新情報"}
}

# ---------------------------------------------------------
# 3. 古いデータの削除（クリーンアップ）
# ---------------------------------------------------------
def cleanup_expired_docs(db):
    """expire_at が現在時刻を過ぎているドキュメントを削除する"""
    now = datetime.datetime.now(timezone.utc)
    collections = ["notification_history", "analysis_logs"]
    
    for coll_name in collections:
        try:
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
# 4. メイン処理：キーワード照合と通知
# ---------------------------------------------------------
def check_keywords_and_notify(content_text, image_ids=None, source="insta"):
    if not content_text:
        return

    image_ids = image_ids or []
    db = firestore.client()
    now = datetime.datetime.now(timezone.utc)
    
    # 期限の設定
    expire_7days = now + timedelta(days=7)
    expire_2days = now + timedelta(days=2)

    # ソース設定の取得（未定義のソースが来た場合のフォールバック付き）
    config = SOURCE_CONFIG.get(source, {"label": f"【{source}】", "title": f"{source}監視"})
    
    print(f"--- ログ保存 & 通知処理開始 (ソース: {source}) ---")

    # --- ステップA: 全体ログの保存 (Webアプリのお知らせ欄用) ---
    try:
        db.collection("analysis_logs").add({
            "content": content_text,
            "image_ids": image_ids, 
            "source": source,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "expire_at": expire_7days
        })
    except Exception as e:
        print(f"解析ログ保存失敗: {e}")

    # --- ステップB: キーワードとユーザーの照合（集約処理） ---
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
            # 購読設定の確認
            subs_docs = list(db.collection("subscriptions").where("user_id", "==", uid).limit(1).stream())
            if not subs_docs:
                continue
                
            sub_data = subs_docs[0].to_dict()
            
            # 通知スイッチの判定 (例: insta_enabled, media_enabled, tweet_enabled)
            enabled_key = f"{source}_enabled"
            if not sub_data.get(enabled_key, True):
                print(f"⏩ ユーザー {uid}: {enabled_key} がOFFのためスキップ")
                continue

            # 送信メッセージの構築
            keyword_str = ", ".join(sorted(list(matched_words)))
            message_body = f"{config['label']} キーワード「{keyword_str}」を発見"

            # 重複送信防止：直近1分間に全く同じメッセージを送っていないか
            one_min_ago = now - timedelta(minutes=1)
            recent_exists = db.collection("notification_history") \
                .where("user_id", "==", uid) \
                .where("source", "==", source) \
                .where("message", "==", message_body) \
                .where("updated_at", ">", one_min_ago) \
                .limit(1).get()

            if recent_exists:
                print(f"⏩ ユーザー {uid}: 同内容を送信済みのたスキップ")
                continue

            # 1. 個別通知履歴（Webの通知一覧用）への保存
            db.collection("notification_history").add({
                "user_id": uid,
                "message": message_body,
                "source": source,
                "keywords": list(matched_words),
                "updated_at": firestore.SERVER_TIMESTAMP,
                "expire_at": expire_2days
            })

            # 2. プッシュ通知(FCM)の送信
            token = sub_data.get("fcm_token")
            if token:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=f"{config['title']} 監視アラート",
                        body=message_body
                    ),
                    token=token,
                )
                messaging.send(message)
                print(f"✅ ユーザー {uid} へ通知送信完了: {keyword_str}")

        except Exception as e:
            print(f"通知送信エラー (UID: {uid}): {e}")

    # --- ステップD: クリーンアップ実行 ---
    cleanup_expired_docs(db)
    
