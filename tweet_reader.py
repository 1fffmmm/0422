import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

def get_drive_service():
    """Google Drive APIの認証"""
    gcp_key_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not gcp_key_str:
        print("エラー: GCP_SERVICE_ACCOUNT_KEY が設定されていません。")
        return None
    try:
        service_account_info = json.loads(gcp_key_str)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Drive API 認証エラー: {e}")
        return None

def get_drive_text(service, file_id):
    """Google Driveからテキストファイルの内容を取得"""
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return fh.getvalue().decode('utf-8')
    except Exception as e:
        print(f"Driveテキスト取得エラー (ID: {file_id}): {e}")
        return ""

def main():
    """
    メイン処理：テキストを取得して返す。
    通知や保存は notifier.py 側で行うため、ここでは実行しません。
    """
    tweet_file_id = os.environ.get("TWEET_FILE_ID")
    
    if not tweet_file_id:
        print("エラー: TWEET_FILE_ID が設定されていません。")
        return None

    drive_service = get_drive_service()
    if not drive_service:
        return None

    print("--- ツイート監視：データ取得開始 ---")
    text_content = get_drive_text(drive_service, tweet_file_id)

    if text_content:
        print(f"取得成功: {len(text_content)} 文字")
        return text_content  # main.py へテキストを渡す
    else:
        print("エラー: ツイート情報が空、または取得に失敗しました。")
        return None

if __name__ == "__main__":
    main()
