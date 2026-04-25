import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

async def get_tomorrow_schedule():
    async with async_playwright() as p:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        url_ym = tomorrow.strftime("%Y%m")
        # 2パターンの日付形式を用意 (04.26 と 4.26)
        search_date_full = tomorrow.strftime("%m.%d")
        search_date_short = f"{tomorrow.month}.{tomorrow.day}"
        
        print(f"=== 実行ログ開始: {now.strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        browser = await p.chromium.launch(headless=True)
        # 画面サイズを大きめに設定（要素が隠れないようにするため）
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        
        url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"
        print(f"アクセス中: {url}")
        
        # ページ遷移
        await page.goto(url, wait_until="networkidle")
        
        # --- 重要：データが読み込まれるまで待機 ---
        # スケジュールの枠組み（.p-media-list__item）が表示されるまで最大10秒待つ
        try:
            await page.wait_for_selector(".p-media-list__item", timeout=10000)
            print("[INFO] スケジュール要素の読み込みを確認しました。")
        except:
            print("[ERROR] タイムアウト：スケジュールが見つかりません。")
            # ページ全体のテキストをデバッグ用に少し出す
            body_text = await page.inner_text("body")
            print(f"ページ冒頭テキスト: {body_text[:100]}...")
            await browser.close()
            return

        # アイテムを全取得
        items = await page.query_selector_all(".p-media-list__item")
        print(f"ページ内の項目数: {len(items)} 件をスキャン中...\n")
        
        tomorrow_schedules = []
        
        for item in items:
            text = await item.inner_text()
            clean_text = " ".join(text.split())
            
            # 両方の形式でチェック
            if (search_date_full in text) or (search_date_short in text):
                print(f"  → ★一致確認: {clean_text[:30]}...")
                tomorrow_schedules.append(clean_text)

        print(f"\n--- 【最終抽出結果: {tomorrow.strftime('%Y年%m月%d日')}】 ---")
        
        if tomorrow_schedules:
            for i, sch in enumerate(tomorrow_schedules, 1):
                print(f"【案件 {i}】\n内容: {sch}\n" + "-"*30)
        else:
            print(f"！！対象日のスケジュールは見つかりませんでした。")

        await browser.close()
        print(f"\n=== 実行ログ終了 ===")

if __name__ == "__main__":
    asyncio.run(get_tomorrow_schedule())
    
