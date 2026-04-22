import os
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from supabase import create_client

def get_drive_text():
    service_account_info = json.loads(os.environ['GCP_SERVICE_ACCOUNT_KEY'])
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('drive', 'v3', credentials=creds)
    file_id = os.environ['DRIVE_FILE_ID']

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    return fh.getvalue().decode('utf-8')

def check_keywords_and_notify(drive_text):
    # Supabaseに接続
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 1. Supabaseから「特定の文字（キーワード）」を取得
    # テーブル名が 'keywords'、カラム名が 'word' と想定
    response = supabase.table("keywords").select("word").execute()
    keywords = [item['word'] for item in response.data]

    print(f"監視中のキーワード: {keywords}")

    # 2. 照合
    found_keywords = []
    for word in keywords:
        if word in drive_text:
            found_keywords.append(word)

    # 3. 結果の出力（後でここに通知処理を追加します）
    if found_keywords:
        print(f"【一致あり】以下の文字が見つかりました: {found_keywords}")
        # TODO: WebPush通知の実行関数をここに呼ぶ
    else:
        print("一致する文字はありませんでした。")

if __name__ == "__main__":
    text = get_drive_text()
    print("--- Drive File Content ---")
    print(text)
    check_keywords_and_notify(text)
