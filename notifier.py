import os
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore, messaging

# ---------------------------------------------------------
# Firebaseの初期化 (既存通り)
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

def delete_old_logs(db):
    # (既存の削除ロジックをここに維持)
    pass

# ---------------------------------------------------------
# メイン処理：source 引数を追加
# ---------------------------------------------------------
def check_keywords_and_notify(content_text, image_ids=None, source="insta"):
    """
    source: "insta" または "media" を受け取る
    """
    if image_ids is None:
        image_ids = []
        
    db = firestore.client()
    print(f"--- 通知処理開始 (ソース: {source}) ---")

    # 1. 共通ログの保存
    try:
        db.collection("analysis_logs").add({
            "content": content_text,
            "image_ids": image_ids, 
            "source": source,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"ログ保存失敗: {e}")

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
            # --- 【重要】ユーザー設定の読み込み ---
            subs_query = db.collection("subscriptions").where("user_id", "==", uid).limit(1).stream()
            subs_docs = list(subs_query)
            
            if not subs_docs:
                print(f"ユーザー {uid} の購読情報が見つからないためスキップします。")
                continue
                
            sub_data = subs_docs[0].to_dict()
            
            # --- 【重要】通知の出し分け判定 ---
            # 例: sourceが "media" なら media_enabled フィールドを確認。デフォルトは True
            is_enabled = sub_data.get(f"{source}_enabled", True)
            
            if not is_enabled:
                print(f"ユーザー {uid} は {source} 通知をオフにしているためスキップします。")
                continue

            # 通知タイトルのカスタマイズ
            display_source = "【インスタ更新】" if source == "insta" else "【メディア出演】"
            keyword_str = ", ".join(matched_words)
            message_body = f"{display_source} キーワード「{keyword_str}」を検知しました"

            # お知らせログへの記録
            db.collection("analysis_logs").add({
                "user_id": uid,
                "message": message_body,
                "source": source,
                "updated_at": firestore.SERVER_TIMESTAMP
            })

            # プッシュ通知送信
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

    delete_old_logs(db)
    
