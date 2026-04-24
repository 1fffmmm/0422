import os
from supabase import create_client
from pywebpush import webpush, WebPushException
import json

def check_keywords_and_notify(drive_text):
    print("--- 2. Supabase 照合 & 通知処理開始 ---")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY")
    
    try:
        supabase = create_client(url, key)
        
        # ログの保存（共通）
        supabase.table("analysis_logs").insert({"content": drive_text}).execute()
        
        # 1. 全ユーザーのキーワードとユーザーIDを取得
        response = supabase.table("keywords").select("word, user_id").execute()
        if not response.data:
            print("キーワードが登録されていません。")
            return

        # 2. Driveテキストに含まれるキーワードを持つユーザーを特定する
        # ユーザーごとの一致したキーワードをまとめる辞書 { "user_id": ["keyword1", "keyword2"] }
        user_matches = {}
        for item in response.data:
            word = item['word']
            user_id = item['user_id']
            if word in drive_text:
                if user_id not in user_matches:
                    user_matches[user_id] = []
                user_matches[user_id].append(word)
        
        if not user_matches:
            print("どのユーザーのキーワードとも一致しませんでした。")
            return

        print(f"【一致したユーザー数】: {len(user_matches)}人")
        
        # 3. 一致したユーザーの購読情報だけを取得して通知を送る
        subs_response = supabase.table("subscriptions").select("*").in_("user_id", list(user_matches.keys())).execute()
        
        for sub in subs_response.data:
            user_id = sub['user_id']
            # そのユーザーに一致したキーワードのリストを取得
            matched_words = user_matches.get(user_id, [])
            
            payload = {
                "title": "監視アラート",
                "body": f"登録キーワード「{', '.join(matched_words)}」が見つかりました。",
                "icon": "/icon.png"
            }

            try:
                webpush(
                    subscription_info = row['subscription_json'],
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": "mailto:your-email@example.com"}
                )
                print(f"通知送信成功: ユーザー {user_id}")
            except WebPushException as ex:
                print(f"通知送信失敗: ユーザー {user_id}, エラー: {ex}")
            
    except Exception as e:
        print(f"ERROR: {e}")
