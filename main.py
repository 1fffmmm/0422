import scraping_media
import scraping_insta  # 先ほど作ったインスタ用スクリプトをインポート
import tweet_reader
import drive_reader    # tweet_readerのために残す
from notifier import check_keywords_and_notify
import os

def main():
    print("===== 統合監視システム 起動 =====")

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

    # --- 2. Instagram 情報の取得 (新システム: Gemini & ImgBB) ---
    print("\n--- [Step 2] Instagram チェック開始 ---")
    try:
        # scraping_insta.py の main関数を呼ぶだけ（内部で通知まで行われます）
        scraping_insta.main()
    except Exception as e:
        print(f"インスタ監視でエラーが発生しました: {e}")

    # --- 3. Twitter(X) 情報の取得 ---
    print("\n--- [Step 3] Twitter (X) チェック開始 ---")
    try:
        # ツイート用にDrive認証を取得
        drive_service = drive_reader.get_drive_service()
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
