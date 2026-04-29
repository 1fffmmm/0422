import scraping_media
import drive_reader
from notifier import check_keywords_and_notify
import os

def main():
    print("===== 統合監視システム 起動 =====")

    # --- 1. メディア情報の取得と通知 ---
    print("\n--- [Step 1] メディア情報チェック開始 ---")
    try:
        # scraping_media.py の main 関数を呼び出す
        # ※内部でFirestore保存と通知(check_keywords_and_notify)まで行われます
        scraping_media.main()
    except Exception as e:
        print(f"メディア監視でエラーが発生しました: {e}")

    # --- 2. Google Drive (インスタ) 情報の取得と通知 ---
    print("\n--- [Step 2] Google Drive チェック開始 ---")
    try:
        drive_service = drive_reader.get_drive_service()
        file_id = os.environ.get("DRIVE_FILE_ID")
        
        drive_text = drive_reader.get_drive_text(drive_service, file_id)
        
        if drive_text:
            print(f"Driveからテキストを取得しました ({len(drive_text)}文字)")
            # インスタ側の通知処理を呼び出す
            check_keywords_and_notify(drive_text, source="insta")
        else:
            print("Driveからテキストを取得できませんでした。")
    except Exception as e:
        print(f"Drive監視でエラーが発生しました: {e}")

    print("\n===== 全ての監視タスクが完了しました =====")

if __name__ == "__main__":
    main()
