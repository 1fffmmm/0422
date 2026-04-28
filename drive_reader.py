import os
import io
import json
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. 初期設定（認証系）
# ==========================================

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

def init_firestore():
    """Firestoreの初期化"""
    try:
        # すでに初期化されている場合はそのアプリを使用
        firebase_admin.get_app()
    except ValueError:
        # 未初期化の場合は環境変数から認証情報を読み込んで初期化
        cred_json = os.environ.get("GCP_SERVICE_ACCOUNT_KEY") # Driveと同じキーを使用する場合
        if not cred_json:
            print("エラー: Firestore認証用の環境変数がありません。")
            return None
        
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

# ==========================================
# 2. Google Drive 操作関数
# ==========================================

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
        return ""

def get_image_ids_from_folder(service, folder_id):
    """指定フォルダ内の .jpg 画像のファイルIDリストを取得する"""
    if not folder_id:
        return []
    
    print(f"--- 2. 画像リスト(フォルダID: {folder_id}) 取得開始 ---")
    image_ids = []
    try:
        query = f"'{folder_id}' in parents and mimeType='image/jpeg' and trashed=false"
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

# ==========================================
# 3. Firestore 保存関数
# ==========================================

def save_to_firestore(db, text, image_ids):
    """取得したデータをFirestoreのanalysis_logsに保存する"""
    print("--- 3. Firestoreへの保存開始 ---")
    try:
        doc_ref = db.collection('analysis_logs').document()
        doc_ref.set({
            'content': text,
            'image_ids': image_ids,
            'source': 'insta',  # インスタ監視であることを明示
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        print(f"Firestore保存成功 (DocID: {doc_ref.id})")
        return True
    except Exception as e:
        print(f"Firestore保存エラー: {e}")
        return False

# ==========================================
# 4. メイン実行処理
# ==========================================

def main():
    # 環境変数から設定を読み込み
    file_id = os.environ.get("DRIVE_FILE_ID")
    folder_id = os.environ.get("DRIVE_FOLDER_ID")
    
    if not file_id:
        print("エラー: DRIVE_FILE_ID が設定されていません。")
        return

    # 1. サービスの初期化
    drive_service = get_drive_service()
    db = init_firestore()
    
    if not drive_service or not db:
        print("サービスの初期化に失敗しました。終了します。")
        return

    # 2. Google Driveからデータ取得
    text_content = get_drive_text(drive_service, file_id)
    image_ids = get_image_ids_from_folder(drive_service, folder_id)

    # 3. Firestoreへ保存
    if text_content:
        save_to_firestore(db, text_content, image_ids)
    else:
        print("保存すべきテキストが見つからなかったため、Firestoreへの保存をスキップしました。")

if __name__ == "__main__":
    main()

