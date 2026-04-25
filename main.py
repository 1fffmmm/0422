from drive_reader import get_drive_text
from notifier import check_keywords_and_notify

def main():
    print("=== 監視ジョブ開始 ===")
    try:
        # 1. Driveから取得
        text = get_drive_text()
        
        # 取得に成功した場合のみ通知処理へ進む
        if text is not None:
            # 2. 照合と通知
            check_keywords_and_notify(text)
        else:
            print("警告: Google Driveからのテキスト取得に失敗したため、通知処理をスキップします。")

    except Exception as e:
        print(f"実行中に予期せぬエラーが発生しました: {e}")
    
    print("=== 監視ジョブ終了 ===")

if __name__ == "__main__":
    main()
