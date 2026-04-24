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
        supabase.table("analysis_logs").insert({"content": drive_text}).execute()
        
        # キーワード取得
        response = supabase.table("keywords").select("word").execute()
        if not response.data:
            print("キーワードが登録されていません。")
            return

        keywords = [item['word'] for item in response.data]
        found_keywords = [word for word in keywords if word in drive_text]
        
        if found_keywords:
            print(f"【一致あり】: {found_keywords}")
            
            # --- WebPush通知処理 ---
            # Supabaseから購読者情報を取得
            subs = supabase.table("subscriptions").select("*").execute()
            
            payload = {
                "title": "監視アラート",
                "body": f"キーワード「{', '.join(found_keywords)}」が見つかりました。",
                "icon": "/icon.png"
            }

            for sub in subs.data:
                try:
                    webpush(
                        subscription_info=json.loads(sub['subscription_json']),
                        data=json.dumps(payload),
                        vapid_private_key=vapid_private_key,
                        vapid_claims={"sub": "mailto:your-email@example.com"}
                    )
                    print(f"通知送信成功: {sub['id']}")
                except WebPushException as ex:
                    print(f"通知送信失敗: {ex}")
        else:
            print("一致なし。")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # 単体テスト用（引数にテキストが必要）
    import sys
    if len(sys.argv) > 1:
        check_keywords_and_notify(sys.argv[1])
