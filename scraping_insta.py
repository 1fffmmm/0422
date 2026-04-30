import os
import shutil
import json
import requests
import instaloader
import firebase_admin
from firebase_admin import credentials
from google import genai
from PIL import Image

# notifier.py から通知・保存関数をインポート
from notifier import check_keywords_and_notify

# --- 環境変数から設定を取得 ---
USER_ID = os.environ.get("INSTA_USER_ID", "jrdebut")
TARGET_PROFILE = os.environ.get("INSTA_TARGET_PROFILE", "jr_official_")
SESSION_ID = os.environ.get("INSTA_SESSION_ID")
SAVE_DIR = "/tmp/insta_downloads"

FIREBASE_SA_KEY_STR = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")

# --- 初期化処理 ---
def initialize_firebase():
    """Firebaseの初期化（Storageは使わないため認証のみ）"""
    if not firebase_admin._apps:
        cred_dict = json.loads(FIREBASE_SA_KEY_STR)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

def analyze_text_with_gemini(image_path):
    """最新の google-genai を使用して画像から文字を抽出する"""
    try:
        # 新しいクライアントの初期化方法
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        img = Image.open(image_path)
        prompt = "この画像内に書かれているテキストをすべて正確に抽出してください。テキストが含まれていない場合は「なし」とだけ出力してください。"
        
        # 新しい generate_content の呼び出し方
        response = client.models.generate_content(
            model='gemini-2.5-flash', # 最新のFlashモデルを指定
            contents=[prompt, img]
        )
        
        text = response.text.strip()
        
        if text and text != "なし":
            return text
        return ""
    except Exception as e:
        print(f"Gemini解析エラー: {e}")
        return ""

def upload_to_imgbb(image_path):
    """画像をImgBBにアップロードし、URLを返す"""
    url = "https://api.imgbb.com/1/upload"
    try:
        with open(image_path, "rb") as file:
            payload = {
                "key": IMGBB_API_KEY,
            }
            files = {
                "image": file
            }
            response = requests.post(url, data=payload, files=files)
            
        if response.status_code == 200:
            return response.json()["data"]["url"]
        else:
            print(f"ImgBBアップロード失敗: {response.text}")
            return None
    except Exception as e:
        print(f"ImgBB通信エラー: {e}")
        return None

def main():
    initialize_firebase()
    
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
        
        # 3. Geminiでの解析とImgBBへのアップロード
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
                
                # 画像をImgBBへアップロード
                image_url = upload_to_imgbb(img_path)
                if image_url:
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
