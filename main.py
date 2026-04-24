from drive_reader import get_drive_text
from notifier import check_keywords_and_notify

def main():
    print("=== 監視ジョブ開始 ===")
    try:
        # 1. Driveから取得
        text = get_drive_text()
        # 2. 照合と通知
        check_keywords_and_notify(text)
    except Exception as e:
        print(f"実行エラー: {e}")
    print("=== 監視ジョブ終了 ===")

if __name__ == "__main__":
    main()
