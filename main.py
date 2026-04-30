import scraping_media
import scraping_insta
import scraping_x
import blog_scraper  # ★追加
from notifier import check_keywords_and_notify
import os

def main():
    print("===== 統合監視システム 起動 =====")

    # --- 1. メディア情報の取得 ---
    print("\n--- [Step 1] メディア情報チェック開始 ---")
    try:
        media_text = scraping_media.main()
        if media_text:
            check_keywords_and_notify(media_text, source="media")
        else:
            print("メディア情報に更新はありませんでした。")
    except Exception as e:
        print(f"メディア監視でエラーが発生しました: {e}")

    # --- 2. Instagram 情報の取得 ---
    print("\n--- [Step 2] Instagram チェック開始 ---")
    try:
        scraping_insta.main()
    except Exception as e:
        print(f"インスタ監視でエラーが発生しました: {e}")

    # --- 3. Twitter(X) 情報の取得 (新システム: サーバー完結型) ---
    print("\n--- [Step 3] Twitter (X) チェック開始 ---")
    try:
        # Drive認証やファイルID取得は不要。直接関数を呼び出す
        scraping_x.run_scraper_and_notify() 
    except Exception as e:
        print(f"ツイート監視でエラーが発生しました: {e}")

    # --- 4. ブログ 情報の取得 (新規追加) ---
    print("\n--- [Step 4] ブログ チェック開始 ---")
    try:
        blog_text = blog_scraper.run_scraper()
        if blog_text:
            # 取得したテキストを通知判定に回す
            check_keywords_and_notify(blog_text, source="blog")
        else:
             print("ブログ情報が取得できませんでした。")
    except Exception as e:
        print(f"ブログ監視でエラーが発生しました: {e}")

    print("\n===== 全ての監視タスクが完了しました =====")

if __name__ == "__main__":
    main()
