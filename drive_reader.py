import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# ファイル1から関数をインポート
from notifier import check_keywords_and_notify

def get_drive_text():
    """
    Google Driveからテキストファイルをダウンロードする
    """
    print("--- 1. Google Drive 処理開始 ---")
    file_id = os.environ.get("DRIVE_FILE_ID")
    gcp_key_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    
    if not gcp_key_str or not file_id:
        print(f"エラー: 環境変数が不足しています (FILE_ID: {file_id})")
        return None

    try:
        service_account_info = json.loads(gcp_key_str)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        service = build('drive', 'v3', credentials=creds)

        print(f"Google Drive(ID: {file_id}) からダウンロード中...")
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        drive_text = fh.getvalue().decode('utf-8')
        print(f"読み込み成功: {len(drive_text)}文字取得しました。")
        return drive_text
    except Exception as e:
        print(f"Driveダウンロードエラー: {e}")
        return None

if __name__ == "__main__":
    print("=== プログラム実行開始 ===")
    
    # 1. Driveからテキスト取得
    text = get_drive_text()
    
    if text is not None:
        # 2. Firebase側の処理を呼び出し
        check_keywords_and_notify(text)
    else:
        print("エラー: テキストが取得できなかったため、処理を中断しました。")
        
    print("=== 全処理終了 ===")
    
