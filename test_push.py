import json
import os
from pywebpush import webpush, WebPushException
from supabase import create_client

# --- 設定（index.htmlと同じもの） ---
SUPABASE_URL = "https://ltqqmclfgdxtasvtirtf.supabase.co"
SUPABASE_KEY = "sb_publishable_iPDG85-2s9n0TBw-kVs55g_xC3ZSt-H"  # もしくはサービスロールキー
# 秘密鍵（Private Key）が必要です！
PRIVATE_VAPID_KEY = "h_Je98KmCdJL-7-2noyW80ApN__yQ1dkdP3h8UFvfW4" 
VAPID_CLAIMS = {"sub": "mailto:test@example.com"}

def send_test_notification():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Supabaseから購読情報を取得
    response = supabase.table("subscriptions").select("*").execute()
    subscriptions = response.data

    if not subscriptions:
        print("購読データがありません。iPhoneでスイッチをONにしてください。")
        return

    print(f"{len(subscriptions)} 件のデバイスに通知を送ります...")

    # 2. 全デバイスに送信
    for sub in subscriptions:
        try:
            # 保存したJSONを復元
            sub_info = sub['subscription_json']
            
            webpush(
                subscription_info=sub_info,
                data=json.dumps({
                    "title": "テスト通知",
                    "body": "Supabaseからの通知テストに成功しました！",
                    "url": "https://www.google.com"
                }),
                vapid_private_key=PRIVATE_VAPID_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            print("送信成功！")
        except WebPushException as ex:
            print(f"送信失敗: {ex}")

if __name__ == "__main__":
    send_test_notification()
  
