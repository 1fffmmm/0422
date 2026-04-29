import scraping_media
import drive_reader
import tweet_reader
from notifier import check_keywords_and_notify
import os

def main():
    print("===== 統合監視システム 起動 =====")
    
    # 後続のステップで使い回すため、ここで初期化
    drive_service = None

    # --- 1. メディア情報の取得 (Web Scraping) ---
    print("\n--- [Step 1] メディア情報チェック開始 ---")
    try:
        media_text = scraping_media.main()
        if media_text:
            check_keywords_and_notify(media_text, source="media")
        else:
            print("メディア情報に更新はありませんでした。")
    except Exception as e:
        print(f"メディア監視でエラーが発生しました: {e}")

    # --- 2. Google Drive (インスタ用) チェック ---
    print("\n--- [Step 2] Google Drive (インスタ) チェック開始 ---")
    try:
        # ここで認証を行う
        drive_service = drive_reader.get_drive_service()
        insta_file_id = os.environ.get("DRIVE_FILE_ID")
        insta_folder_id = os.environ.get("DRIVE_FOLDER_ID")
        
        if insta_file_id:
            drive_text = drive_reader.get_drive_text(drive_service, insta_file_id)
            if drive_text:
                image_ids = drive_reader.get_image_ids_from_folder(drive_service, insta_folder_id)
                print(f"Insta用テキストを取得しました ({len(drive_text)}文字 / 画像 {len(image_ids)}件)")
                check_keywords_and_notify(drive_text, image_ids=image_ids, source="insta")
            else:
                print("Insta用テキストを取得できませんでした。")
    except Exception as e:
        print(f"インスタ監視でエラーが発生しました: {e}")

    # --- 3. Twitter(X) 情報の取得 (tweet_reader を使用) ---
    print("\n--- [Step 3] Twitter (X) チェック開始 ---")
    try:
        # 【修正ポイント！】
        # 1. get_latest_tweets() ではなく main() を呼ぶ
        # 2. 引数に drive_service を渡して認証を使い回す
        tweet_text = tweet_reader.main(drive_service=drive_service) 
        
        if tweet_text:
            print(f"最新ツイート用テキストを取得しました ({len(tweet_text)}文字)")
            check_keywords_and_notify(tweet_text, source="tweet")
        else:
            print("ツイート情報が見つからないか、エラーが発生しました。")
    except Exception as e:
        print(f"ツイート監視でエラーが発生しました: {e}")

    print("\n===== 全ての監視タスクが完了しました =====")

if __name__ == "__main__":
    main()
    
