import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# notifier.py から通知・保存関数をインポート
from notifier import check_keywords_and_notify

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
        
        # 取得したバイナリをテキスト(utf-8)にデコード
        return fh.getvalue().decode('utf-8')
    except Exception as e:
        print(f"Driveテキスト取得エラー (ID: {file_id}): {e}")
        return ""

def main():
    # GitHub Secretsに登録した TWEET_FILE_ID を取得
    tweet_file_id = os.environ.get("TWEET_FILE_ID")
    
    if not tweet_file_id:
        print("エラー: TWEET_FILE_ID が環境変数に設定されていません。")
        return

    drive_service = get_drive_service()
    if not drive_service:
        return

    print("--- ツイート監視 開始 ---")

    # 1. Google Driveからツイート情報のテキストを取得
    text_content = get_drive_text(drive_service, tweet_file_id)

    # 2. キーワード照合と通知の実行
    if text_content:
        print(f"取得データ: {text_content[:50]}...") # 冒頭のみログ表示
        
        # ツイート監視なので source="tweet" を指定
        # 画像はないため image_ids は None または空リストを渡します
        check_keywords_and_notify(text_content, image_ids=None, source="tweet")
        
        print("--- ツイート監視 完了 ---")
    else:
        print("エラー: ツイート情報が空、または取得に失敗しました。")

if __name__ == "__main__":
    main()
