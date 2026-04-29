import scraping_media
import drive_reader
from notifier import check_keywords_and_notify
import os

def main():
    print("===== 統合監視システム 起動 =====")

    # --- 1. メディア情報の取得と通知 (Web Scraping) ---
    print("\n--- [Step 1] メディア情報チェック開始 ---")
    try:
        media_text = scraping_media.main()
        if media_text:
            check_keywords_and_notify(media_text, source="media")
        else:
            print("メディア情報に更新はありませんでした。")
    except Exception as e:
        print(f"メディア監視でエラーが発生しました: {e}")

    # --- 2. Google Drive (インスタ) 情報の取得と通知 ---
    print("\n--- [Step 2] Google Drive (インスタ) チェック開始 ---")
    try:
        drive_service = drive_reader.get_drive_service()
        insta_file_id = os.environ.get("DRIVE_FILE_ID")
        # 以前のコードにある folder_id (画像取得用)
        insta_folder_id = os.environ.get("DRIVE_FOLDER_ID")
        
        if insta_file_id:
            drive_text = drive_reader.get_drive_text(drive_service, insta_file_id)
            if drive_text:
                # インスタ監視は画像がある可能性を考慮して image_ids を取得
                image_ids = drive_reader.get_image_ids_from_folder(drive_service, insta_folder_id)
                print(f"Insta用テキストを取得しました ({len(drive_text)}文字 / 画像 {len(image_ids)}件)")
                check_keywords_and_notify(drive_text, image_ids=image_ids, source="insta")
            else:
                print("Insta用テキストを取得できませんでした。")
        else:
            print("DRIVE_FILE_ID が設定されていないためスキップします。")
    except Exception as e:
        print(f"インスタ監視でエラーが発生しました: {e}")

    # --- 3. Google Drive (ツイート) 情報の取得と通知 ---
    print("\n--- [Step 3] Google Drive (ツイート) チェック開始 ---")
    try:
        # drive_service は共通で使用可能
        tweet_file_id = os.environ.get("TWEET_FILE_ID")
        
        if tweet_file_id:
            tweet_text = drive_reader.get_drive_text(drive_service, tweet_file_id)
            if tweet_text:
                print(f"ツイート用テキストを取得しました ({len(tweet_text)}文字)")
                # ツイート監視は画像なしとして image_ids=None (source="tweet")
                check_keywords_and_notify(tweet_text, image_ids=None, source="tweet")
            else:
                print("ツイート用テキストを取得できませんでした。")
        else:
            print("TWEET_FILE_ID が設定されていないためスキップします。")
    except Exception as e:
        print(f"ツイート監視でエラーが発生しました: {e}")

    print("\n===== 全ての監視タスクが完了しました =====")

if __name__ == "__main__":
    main()
    
