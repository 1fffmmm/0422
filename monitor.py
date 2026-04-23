import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client
from pywebpush import webpush, WebPushException

def get_drive_text():
    print("--- 1. Google Drive 処理開始 ---")
    file_id = os.environ.get("DRIVE_FILE_ID")
    service_account_info = eval(os.environ.get("GCP_SERVICE_ACCOUNT_KEY"))
    
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('drive', 'v3', credentials=creds)

    print("Google Driveからファイルをダウンロード中...")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    drive_text = fh.getvalue().decode('utf-8')
    print(f"Google Driveからの読み込み成功（文字数: {len(drive_text)}文字）")
    return drive_text

def check_keywords_and_notify(drive_text):
    print("--- 2. Supabase 照合と通知処理開始 ---")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    vapid_private_key = os.environ.get("VAPID_PRIVATE_KEY") # 秘密鍵を取得
    
    try:
        supabase = create_client(url, key)
        
        # 解析結果の保存
        supabase.table("analysis_logs").insert({"content": drive_text}).execute()
        
        # キーワードの照合
        response = supabase.table("keywords").select("word").execute()
        if not response.data:
            print("【警告】監視対象キーワードが登録されていません。")
            return

        keywords = [item['word'] for item in response.data]
        found_keywords = [word for word in keywords if word in drive_text]
        
        print("==============================")
        if found_keywords:
            print(f"【一致あり】見つかった文字: {found_keywords}")
            print("プッシュ通知の送信を開始します...")
            
            # Supabaseから購読者（通知先）を取得
            subs_response = supabase.table("subscriptions").select("*").execute()
            subscribers = subs_response.data
            
            if not subscribers:
                print("通知の送信先（購読者）が誰も登録されていません。")
            else:
                for sub in subscribers:
                    try:
                        sub_info = sub['subscription_json']
                        # 通知の中身を作成
                        message_text = f"キーワード「{', '.join(found_keywords)}」を検知しました！"
                        payload = json.dumps({"title": "監視アラート", "body": message_text})
                        
                        # WebPush送信
                        webpush(
                            subscription_info=sub_info,
                            data=payload,
                            vapid_private_key=vapid_private_key,
                            vapid_claims={"sub": "mailto:admin@example.com"} # 必須項目
                        )
                        print("通知送信成功！")
                    except WebPushException as ex:
                        print(f"通知送信失敗: {ex}")
        else:
            print("一致する文字はありませんでした。")
        print("==============================")
            
    except Exception as e:
        print(f"ERROR: 処理中にエラーが発生しました: {e}")
    
    print("--- 3. 全ての処理が終了しました ---")

if __name__ == "__main__":
    print("プログラムを起動しました。")
    text = get_drive_text()
    check_keywords_and_notify(text)
    
