import os
import shutil
import io
import json
import instaloader
from google.cloud import vision
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials, storage

# notifier.py から通知・保存関数をインポート
from notifier import check_keywords_and_notify

# --- 環境変数から設定を取得 (サーバー運用向け) ---
USER_ID = os.environ.get("INSTA_USER_ID", "jrdebut")
TARGET_PROFILE = os.environ.get("INSTA_TARGET_PROFILE", "jr_official_")
SESSION_ID = os.environ.get("INSTA_SESSION_ID")

# サーバーの一時ディレクトリを使用（GitHub ActionsやCloud Run等では /tmp が一般的）
SAVE_DIR = "/tmp/insta_downloads"

# Firebase と GCP の認証情報 (JSON文字列として環境変数に保存)
GCP_SA_KEY_STR = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
FIREBASE_SA_KEY_STR = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET") # 例: your-project-id.appspot.com

# --- 初期化処理 ---
def initialize_firebase():
    """Firebaseの初期化 (Storageバケットを含む)"""
    if not firebase_admin._apps:
        cred_dict = json.loads(FIREBASE_SA_KEY_STR)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': FIREBASE_STORAGE_BUCKET
        })

def get_vision_client():
    """Vision APIクライアントの初期化"""
    info = json.loads(GCP_SA_KEY_STR)
    creds = service_account.Credentials.from_service_account_info(info)
    return vision.ImageAnnotatorClient(credentials=creds)

def analyze_text(client, image_path):
    """Vision APIを使用して画像から文字を抽出する"""
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    return texts[0].description if texts else ""

def upload_to_firebase_storage(local_image_path, filename):
    """画像をFirebase Storageにアップロードし、URLを返す"""
    bucket = storage.bucket()
    blob = bucket.blob(f"instagram_stories/{TARGET_PROFILE}/{filename}")
    blob.upload_from_filename(local_image_path)
    blob.make_public() # 必要に応じて公開設定
    return blob.public_url

def main():
    initialize_firebase()
    vision_client = get_vision_client()

    # 1. フォルダの準備（既存データのクリア）
    if os.path.exists(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.makedirs(SAVE_DIR)

    # 2. Instaloaderの設定とダウンロード
    L = instaloader.Instaloader(
        dirname_pattern=SAVE_DIR,
        filename_pattern='{date_utc:%H%M%S}_{shortcode}',
        download_videos=True,
        download_video_thumbnails=True,
        save_metadata=False,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )

    try:
        print("Instagramにアクセス中...")
        L.context._session.cookies.set('sessionid', SESSION_ID, domain='.instagram.com')
        L.context.username = USER_ID
        profile = instaloader.Profile.from_username(L.context, TARGET_PROFILE)

        print(f"最新ストーリーを取得中: {TARGET_PROFILE}")
        L.download_stories(userids=[profile.userid])
        
        # 3. Vision APIでの解析とFirebase Storageへの画像アップロード
        print("画像の解析とアップロードを実行しています...")
        results_text = ""
        uploaded_image_urls = []

        for filename in sorted(os.listdir(SAVE_DIR)):
            if filename.endswith(".jpg"):
                img_path = os.path.join(SAVE_DIR, filename)
                
                # 文字解析
                text = analyze_text(vision_client, img_path)
                if text:
                    results_text += f"【ファイル名: {filename}】\n{text}\n" + "="*30 + "\n"
                
                # 画像をFirebase Storageへアップロード
                image_url = upload_to_firebase_storage(img_path, filename)
                uploaded_image_urls.append(image_url)

        # 4. notifier.py の関数を呼び出して保存と通知を実行
        if results_text:
            print("解析完了。通知とデータベース保存を実行します。")
            # Google DriveのファイルIDの代わりに、Firebase StorageのURLリストを渡す
            check_keywords_and_notify(results_text, uploaded_image_urls, source="insta")
        else:
            print("解析可能な文字は見つかりませんでした。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
  
