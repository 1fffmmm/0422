import os
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client

def get_drive_text():
    print("--- 1. Google Drive 処理開始 ---")
    file_id = os.environ.get("DRIVE_FILE_ID")
    service_account_info = eval(os.environ.get("GCP_SERVICE_ACCOUNT_KEY"))
    
    print(f"DEBUG: 取得対象ファイルID: {file_id}")
    
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
    print("-------------------------------")
    return drive_text

def check_keywords_and_notify(drive_text):
    print("--- 2. Supabase 照合処理開始 ---")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    print(f"DEBUG: Supabase接続先: {url}")
    
    try:
        supabase = create_client(url, key)
        
        print("Supabaseからキーワードを取得しています...")
        response = supabase.table("keywords").select("word").execute()
        
        if not response.data:
            print("【警告】Supabaseのテーブルにキーワードが1件も登録されていません。")
            return

        keywords = [item['word'] for item in response.data]
        print(f"監視対象キーワード（{len(keywords)}件）: {keywords}")

        print("照合を実行中...")
        found_keywords = [word for word in keywords if word in drive_text]
        
        print("==============================")
        if found_keywords:
            print(f"【一致あり】見つかった文字: {found_keywords}")
            # ここにWebPush通知のコードを後ほど追加できます
        else:
            print("一致する文字はありませんでした。")
        print("==============================")
            
    except Exception as e:
        print(f"ERROR: Supabase連携中にエラーが発生しました: {e}")
    
    print("--- 3. 全ての処理が終了しました ---")

if __name__ == "__main__":
    print("プログラムを起動しました。")
    try:
        text = get_drive_text()
        check_keywords_and_notify(text)
    except Exception as e:
        print(f"実行中に予期せぬエラーが発生しました: {e}")
