import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

def get_drive_text():
    # GitHub Secretsから認証情報を取得 [cite: 6]
    service_account_info = json.loads(os.environ['GCP_SERVICE_ACCOUNT_KEY'])
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    
    service = build('drive', 'v3', credentials=creds)
    file_id = os.environ['DRIVE_FILE_ID'] # 

    # ファイルのダウンロード
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    # テキストとしてデコード
    content = fh.getvalue().decode('utf-8')
    return content

if __name__ == "__main__":
    text = get_drive_text()
    print("--- Drive File Content ---")
    print(text)
    # ここに後ほどSupabaseとの照合ロジックを追加します [cite: 7]
