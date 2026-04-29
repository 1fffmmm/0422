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
# 2. 古い通知履歴の削除（無料プラン用：手動クリーンアップ）
# ---------------------------------------------------------
def delete_old_notifications(db):
    """
    notification_history コレクションから2日以上前のドキュメントを削除する
    """
    try:
        # 2日前の境界線を計算
        now = datetime.datetime.now(timezone.utc)
        cutoff = now - timedelta(days=2)

        # updated_at が cutoff（2日前）より古いものを検索
        old_docs = db.collection("notification_history")\
                     .where("updated_at", "<", cutoff)\
                     .stream()

        deleted_count = 0
        for doc in old_docs:
            doc.reference.delete()
            deleted_count += 1
        
        if deleted_count > 0:
            print(f"🗑️ クリーンアップ完了: 古い通知履歴を {deleted_count} 件削除しました。")
    except Exception as e:
        # インデックス未作成エラーが出る場合は、ログのURLから作成が必要です
        print(f"履歴削除エラー: {e}")

# ---------------------------------------------------------
# 3. メイン処理：キーワード照合と通知
# ---------------------------------------------------------
def check_keywords_and_notify(content_text, image_ids=None, source="insta"):
    """
    content_text: 解析されたテキスト
    image_ids: 画像IDのリスト
    source: "insta" または "media"
    """
    if image_ids is None:
        image_ids = []
        
    db = firestore.client()
    print(f"--- 通知処理開始 (ソース: {source}) ---")

    # --- ステップA: 全体ログの保存 (Web画面のメイン表示用) ---
    try:
        db.collection("analysis_logs").add({
            "content": content_text,
            "image_ids": image_ids, 
            "source": source,
            "updated_at": firestore.SERVER_TIMESTAMP
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
            # ユーザー設定の取得
            subs_query = db.collection("subscriptions").where("user_id", "==", uid).limit(1).stream()
            subs_docs = list(subs_query)
            
            if not subs_docs:
                continue
                
            sub_data = subs_docs[0].to_dict()
            
            # 通知のオンオフ判定 (insta_enabled / media_enabled)
            is_enabled = sub_data.get(f"{source}_enabled", True)
            if not is_enabled:
                print(f"ユーザー {uid} は {source} 通知をオフにしているためスキップ。")
                continue

            # 通知内容の構成
            display_source = "【インスタ更新】" if source == "insta" else "【メディア出演】"
            keyword_str = ", ".join(matched_words)
            message_body = f"{display_source} キーワード「{keyword_str}」を検知しました"

            # 1. 個別通知履歴への保存 (2日で自動削除対象)
            db.collection("notification_history").add({
                "user_id": uid,
                "message": message_body,
                "source": source,
                "updated_at": firestore.SERVER_TIMESTAMP
            })

            # 2. プッシュ通知の送信 (FCM)
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
                print(f"✅ ユーザー {uid} へ通知を送信しました。")

        except Exception as e:
            print(f"通知送信エラー (UID: {uid}): {e}")

    # --- ステップD: 古いデータのクリーンアップ実行 ---
    delete_old_notifications(db)
