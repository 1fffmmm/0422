import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# notifier.py から通知・保存関数をインポート
from notifier import check_keywords_and_notify

def get_drive_service():
    gcp_key_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not gcp_key_str: return None
    try:
        service_account_info = json.loads(gcp_key_str)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Drive API 認証エラー: {e}"); return None

def get_drive_text(service, file_id):
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return fh.getvalue().decode('utf-8')
    except Exception as e:
        print(f"Driveテキスト取得エラー: {e}"); return ""

def get_image_ids_from_folder(service, folder_id):
    if not folder_id: return []
    image_ids = []
    try:
        query = f"'{folder_id}' in parents and mimeType='image/jpeg' and trashed=false"
        results = service.files().list(q=query, fields='files(id, name)').execute()
        for item in results.get('files', []):
            image_ids.append(item['id'])
        return image_ids
    except Exception as e:
        print(f"Drive画像取得エラー: {e}"); return []

def main():
    file_id = os.environ.get("DRIVE_FILE_ID")
    folder_id = os.environ.get("DRIVE_FOLDER_ID")
    
    if not file_id:
        print("エラー: DRIVE_FILE_ID が未設定です。")
        return

    drive_service = get_drive_service()
    if not drive_service: return

    # 1. Google Driveからデータ取得
    text_content = get_drive_text(drive_service, file_id)
    image_ids = get_image_ids_from_folder(drive_service, folder_id)

    # 2. notifier.py の関数を呼び出して保存と通知を一括実行
    if text_content:
        # ここで source="insta" を指定。必要に応じて使い分けてください。
        check_keywords_and_notify(text_content, image_ids, source="insta")
    else:
        print("処理対象のテキストがないため終了します。")

if __name__ == "__main__":
    main()
