import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

def main():
    # 1. GitHub Secretsから情報を取得
    service_account_info = json.loads(os.environ["GCP_SERVICE_ACCOUNT_KEY"])
    file_id = os.environ["DRIVE_FILE_ID"]

    # 2. Google Drive APIの認証
    creds = service_account.Credentials.from_service_account_info(service_account_info)
    service = build('drive', 'v3', credentials=creds)

    # 3. ファイルのダウンロード
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    # 4. 内容の表示（確認用）
    content = fh.getvalue().decode('utf-8')
    print("--- ファイルの内容 ---")
    print(content)
    print("----------------------")

if __name__ == "__main__":
    main()
