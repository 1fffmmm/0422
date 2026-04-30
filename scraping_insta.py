import os
import shutil
import json
from datetime import datetime, timedelta, timezone
import instaloader
import firebase_admin
from firebase_admin import credentials, storage
import google.generativeai as genai
from PIL import Image

# notifier.py から通知・保存関数をインポート
from notifier import check_keywords_and_notify

# --- 環境変数から設定を取得 ---
USER_ID = os.environ.get("INSTA_USER_ID", "jrdebut")
TARGET_PROFILE = os.environ.get("INSTA_TARGET_PROFILE", "jr_official_")
SESSION_ID = os.environ.get("INSTA_SESSION_ID")
SAVE_DIR = "/tmp/insta_downloads"

FIREBASE_SA_KEY_STR = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 初期化処理 ---
def initialize_firebase():
    """Firebaseの初期化"""
    if not firebase_admin._apps:
        cred_dict = json.loads(FIREBASE_SA_KEY_STR)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': FIREBASE_STORAGE_BUCKET
        })

def cleanup_expired_storage_images():
    """【お掃除機能】Firebase Storage内の7日以上古い画像を自動削除する"""
    bucket = storage.bucket()
    blobs = bucket.list_blobs(prefix=f"instagram_stories/{TARGET_PROFILE}/")
    now = datetime.now(timezone.utc)
    deleted_count = 0
    
    for blob in blobs:
        if blob.time_created and (now - blob.time_created > timedelta(days=7)):
            try:
                blob.delete()
                deleted_count += 1
            except Exception as e:
                print(f"画像削除エラー ({blob.name}): {e}")
                
    if deleted_count > 0:
        print(f"🗑️ Firebase Storageから古い画像を {deleted_count} 件削除しました。")

def analyze_text_with_gemini(image_path):
    """Gemini 1.5 Flashを使用して画像から文字を抽出する"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img = Image.open(image_path)
        # Geminiへの指示（プロンプト）
        prompt = "この画像内に書かれているテキストをすべて正確に抽出してください。テキストが含まれていない場合は「なし」とだけ出力してください。"
        
        response = model.generate_content([prompt, img])
        text = response.text.strip()
        
        if text and text != "なし":
            return text
        return ""
    except Exception as e:
        print(f"Gemini解析エラー: {e}")
        return ""

def upload_to_firebase_storage(local_image_path, filename):
    """画像をFirebase Storageにアップロードし、URLを返す"""
    bucket = storage.bucket()
    blob = bucket.blob(f"instagram_stories/{TARGET_PROFILE}/{filename}")
    blob.upload_from_filename(local_image_path)
    blob.make_public()
    return blob.public_url

def main():
    initialize_firebase()
    
    # 実行のたびに古い画像を削除して無料枠（5GB）を維持
    cleanup_expired_storage_images()

    # 1. フォルダの準備
    if os.path.exists(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.makedirs(SAVE_DIR)

    # 2. Instaloaderの設定
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
        
        # 3. Geminiでの解析とStorageへのアップロード
        print("Geminiによる画像解析とアップロードを実行しています...")
        results_text = ""
        uploaded_image_urls = []

        for filename in sorted(os.listdir(SAVE_DIR)):
            if filename.endswith(".jpg"):
                img_path = os.path.join(SAVE_DIR, filename)
                
                # Geminiで文字解析
                text = analyze_text_with_gemini(img_path)
                if text:
                    results_text += f"【ファイル名: {filename}】\n{text}\n" + "="*30 + "\n"
                
                # 画像をFirebase Storageへアップロード
                image_url = upload_to_firebase_storage(img_path, filename)
                uploaded_image_urls.append(image_url)

        # 4. 通知と保存
        if results_text:
            print("解析完了。通知とデータベース保存を実行します。")
            check_keywords_and_notify(results_text, uploaded_image_urls, source="insta")
        else:
            print("解析可能な文字は見つかりませんでした。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
    
