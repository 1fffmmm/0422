import os
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

def get_drive_text():
    print("--- 1. Google Drive 処理開始 ---")
    file_id = os.environ.get("DRIVE_FILE_ID")
    service_account_info = eval(os.environ.get("GCP_SERVICE_ACCOUNT_KEY"))
    
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('drive', 'v3', credentials=creds)

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    drive_text = fh.getvalue().decode('utf-8')
    print(f"Google Driveからの読み込み成功（{len(drive_text)}文字）")
    return drive_text

if __name__ == "__main__":
    # 単体テスト用
    print(get_drive_text())
  
