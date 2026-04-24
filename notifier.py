import firebase_admin
from firebase_admin import credentials, firestore, messaging
import os
import json

# Firebaseの初期化（GitHub Secretsのサービスアカウントを使用）
if not firebase_admin._apps:
    cred_json = os.environ.get('GCP_SERVICE_ACCOUNT_KEY')
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    else:
        raise ValueError("GCP_SERVICE_ACCOUNT_KEY が設定されていません")

db = firestore.client()

def check_keywords_and_notify(drive_text):
    print("=== Firestore 照合 & FCM通知処理を開始 ===")
    
    # 1. 全ユーザーのキーワード設定を取得
    keywords_ref = db.collection('keywords')
    docs = keywords_ref.stream()
    
    user_matches = {}
    for doc in docs:
        data = doc.to_dict()
        uid = data.get('user_id')
        word = data.get('keyword') or data.get('word') # 両方の可能性に対応
        if uid and word and word in drive_text:
            if uid not in user_matches:
                user_matches[uid] = []
            user_matches[uid].append(word)

    # 2. 一致したユーザーに通知を送信
    for uid, matched_words in user_matches.items():
        print(f"一致確認 (User: {uid}): {matched_words}")
        send_fcm_notification(uid, matched_words)

    # 3. 解析ログをFirestoreに保存（フロントエンド表示用）
    try:
        db.collection('analysis_logs').add({
            'content': drive_text,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"ログ保存エラー: {e}")

def send_fcm_notification(user_id, matched_keywords):
    # そのユーザーに紐づくFCMトークンを取得
    subs_ref = db.collection('subscriptions').where('user_id', '==', user_id)
    tokens = [doc.to_dict().get('fcm_token') for doc in subs_ref.stream() if doc.to_dict().get('fcm_token')]

    if not tokens:
        print(f"通知先トークンが見つかりません: {user_id}")
        return

    message_body = f"登録キーワード「{', '.join(matched_keywords)}」が見つかりました。"
    
    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(
                title='監視アラート',
                body=message_body
            ),
            token=token
        )
        try:
            response = messaging.send(message)
            print(f"通知送信成功: {response}")
        except Exception as e:
            print(f"通知送信エラー ({token}): {e}")
