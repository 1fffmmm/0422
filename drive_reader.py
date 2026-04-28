import os
import io
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload

# ※ ファイル1から関数をインポート（Firebase処理側）

def get_drive_service():
    """Google Drive APIのサービスオブジェクトを作成する"""
    gcp_key_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not gcp_key_str:
        print("エラー: 環境変数 GCP_SERVICE_ACCOUNT_KEY が設定されていません。")
        return None
        
    try:
        service_account_info = json.loads(gcp_key_str)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Drive API 認証エラー: {e}")
        return None

def get_drive_text(service, file_id):
    """Google Driveからテキストファイルをダウンロードする"""
    print(f"--- 1. テキストファイル(ID: {file_id}) 取得開始 ---")
    try:
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
        print(f"Driveテキストダウンロードエラー: {e}")
        return None

def get_image_ids_from_folder(service, folder_id):
    """指定フォルダ内の .jpg 画像のファイルIDリストを取得する"""
    print(f"--- 2. 画像リスト(フォルダID: {folder_id}) 取得開始 ---")
    image_ids = []
    try:
        # mimeType='image/jpeg' で jpg 画像のみを指定、trashed=false でゴミ箱の中身を除外
        query = f"'{folder_id}' in parents and mimeType='image/jpeg' and trashed=false"
        
        # APIを呼び出してファイル一覧を取得
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageSize=100
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print("フォルダ内に画像が見つかりませんでした。")
        else:
            for item in items:
                image_ids.append(item['id'])
                print(f"画像発見: {item['name']} (ID: {item['id']})")
                
        print(f"合計 {len(image_ids)} 枚の画像IDを取得しました。")
        return image_ids
        
    except Exception as e:
        print(f"Drive画像リスト取得エラー: {e}")
        return []

