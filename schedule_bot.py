import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

async def get_tomorrow_schedule():
    async with async_playwright() as p:
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        url_ym = tomorrow.strftime("%Y%m")
        search_date_full = tomorrow.strftime("%m.%d")
        search_date_short = f"{tomorrow.month}.{tomorrow.day}"
        
        print(f"=== 実行ログ開始: {now.strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        # ブラウザの起動（偽装設定を追加）
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"
        print(f"アクセス中: {url}")
        
        # タイムアウトを長めに設定し、ネットワークが落ち着くまで待つ
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            
            # 少し待機（JavaScriptが完全に実行されるのを待つ）
            await page.wait_for_timeout(5000) 
            
            # .p-media-list__item が出るまで、あるいは body 全体がロードされるまで待つ
            await page.wait_for_selector(".p-media-list__item", timeout=20000)
            print("[INFO] スケジュール要素を確認しました。")
            
        except Exception as e:
            print(f"[ERROR] 読み込みに失敗しました。")
            # 失敗した時のページタイトルを確認
            title = await page.title()
            print(f"現在のページタイトル: {title}")
            await browser.close()
            return

        items = await page.query_selector_all(".p-media-list__item")
        print(f"ページ内の項目数: {len(items)} 件をスキャン中...\n")
        
        tomorrow_schedules = []
        for item in items:
            text = await item.inner_text()
            clean_text = " ".join(text.split())
            if (search_date_full in text) or (search_date_short in text):
                print(f"  → ★一致確認: {clean_text[:50]}...")
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
    
