import os
import traceback

# 修正したファイルから、必要な関数をすべて読み込む
from drive_reader import get_drive_service, get_drive_text, get_image_ids_from_folder
from notifier import check_keywords_and_notify

def main():
    print("=== 監視ジョブ開始 ===")
    try:
        # 1. 環境変数からIDを取得
        FILE_ID = os.environ.get("DRIVE_FILE_ID")
        # 以前教えていただいたフォルダIDをデフォルトに設定
        FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "1oFKFlM7P9szbG0u8SZe2UTlrA7ZWYMtZ")
        
        if not FILE_ID:
            print("エラー: 環境変数 DRIVE_FILE_ID が設定されていません。")
            return

        # 2. Drive APIの窓口（サービス）を1回だけ作成
        print("Drive APIの認証を行っています...")
        service = get_drive_service()
        
        if service:
            # 3. テキストを取得
            text = get_drive_text(service, FILE_ID)
            
            # 4. 画像IDリストを取得
            image_ids = get_image_ids_from_folder(service, FOLDER_ID)
            
            # 5. Firebaseへ保存・通知処理（ここで古いログの削除も実行されます）
            if text is not None:
                check_keywords_and_notify(text, image_ids)
            else:
                print("警告: Google Driveからのテキスト取得に失敗したため、通知処理をスキップします。")
        else:
            print("エラー: Driveの認証に失敗したため、処理を中断します。")

    except Exception as e:
        print(f"実行中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()  # 詳しいエラー場所を表示

    print("=== 監視ジョブ終了 ===")

if __name__ == "__main__":
    main()
