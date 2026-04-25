import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

async def get_tomorrow_schedule():
    async with async_playwright() as p:
        # 1. 日付の計算とログ表示
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        url_ym = tomorrow.strftime("%Y%m")
        search_date = tomorrow.strftime("%m.%d")
        
        print(f"==========================================")
        print(f" 実行日時: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" 取得対象日: {tomorrow.strftime('%Y-%m-%d')} ({search_date})")
        print(f" ターゲットURL: https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}")
        print(f"==========================================\n")
        
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"[INFO] ページ読み込み中...")
        await page.goto(f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}", wait_until="networkidle")
        print(f"[INFO] 読み込み完了。データを抽出します。\n")

        # 抽出ロジック
        items = await page.query_selector_all(".p-media-list__item")
        
        found_count = 0
        for item in items:
            text = await item.inner_text()
            if search_date in text:
                found_count += 1
                print(f"【一致案件 {found_count}】")
                print(text.strip())
                print("-" * 30)

        if found_count == 0:
            print(f"[RESULT] {search_date} のスケジュールは見つかりませんでした。")
        else:
            print(f"\n[RESULT] 合計 {found_count} 件のスケジュールを抽出しました。")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_tomorrow_schedule())
