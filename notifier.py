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
        
        # ログの保存
        try:
            supabase.table("analysis_logs").insert({"content": drive_text}).execute()
        except Exception as log_err:
            print(f"ログ保存エラー（続行します）: {log_err}")
        
        # 1. キーワード取得
        response = supabase.table("keywords").select("word, user_id").execute()
        if not response.data:
            print("キーワードが登録されていません。")
            return

        # 2. マッチング処理
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
        
        # 3. 通知送信ループ
        subs_response = supabase.table("subscriptions").select("*").in_("user_id", list(user_matches.keys())).execute()
        
        for sub in subs_response.data:
            # --- ループ内全体を try-except で囲む ---
            try:
                user_id = sub['user_id']
                matched_words = user_matches.get(user_id, [])
                
                payload = {
                    "title": "監視アラート",
                    "body": f"登録キーワード「{', '.join(matched_words)}」が見つかりました。",
                    "icon": "/icon.png"
                }

                # 通知送信
                webpush(
                    subscription_info = sub['subscription_json'],
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": "mailto:your-email@example.com"}
                )
                print(f"通知送信成功: ユーザー {user_id}")

            except WebPushException as ex:
                # ブラウザ側の期限切れやエンドポイントエラーなど
                print(f"通知送信失敗 (WebPushエラー): ユーザー {user_id}, 内容: {ex}")
            except Exception as e:
                # それ以外の予期せぬエラー（データ形式の不備など）
                print(f"通知処理中の予期せぬエラー: ユーザー {user_id}, エラー: {e}")
                # continue は書かなくても次のループへ進みますが、明示的に書くことも可能です
                continue 

    except Exception as e:
        # DB接続自体に失敗した場合など、致命的なエラーのみここでキャッチ
        print(f"致命的なエラーが発生しました: {e}")
