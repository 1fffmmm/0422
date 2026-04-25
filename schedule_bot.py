import asyncio
import os
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
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 1200}
        )
        page = await context.new_page()
        
        url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"
        print(f"アクセス中: {url}")
        
        try:
            # ページに移動。domcontentloadedまで待つ
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 完全に読み込まれるまで少し待つ
            await page.wait_for_timeout(7000) 
            
            # スケジュールの要素が出るまで待機（より広い範囲のクラス .p-media-list も候補に入れる）
            await page.wait_for_selector(".p-media-list, .p-media-list__item", timeout=30000)
            print("[INFO] スケジュールリストの表示を確認しました。")
            
        except Exception as e:
            print(f"[ERROR] タイムアウトまたは要素未発見。")
            # デバッグ用にスクリーンショットを保存（GitHub Actionsのファイルとして残せます）
            await page.screenshot(path="debug_screen.png")
            print("デバッグ用スクリーンショットを保存しました（debug_screen.png）")
            await browser.close()
            return

        # アイテムを全取得（タグ名 article も含めて広く取得）
        items = await page.query_selector_all(".p-media-list__item, article")
        print(f"スキャン対象: {len(items)} 件\n")
        
        tomorrow_schedules = []
        for item in items:
            text = await item.inner_text()
            if not text: continue
            
            clean_text = " ".join(text.split())
            if (search_date_full in text) or (search_date_short in text):
                # 重複を避ける
                if clean_text not in tomorrow_schedules:
                    print(f"  → ★一致確認: {clean_text[:50]}...")
                    tomorrow_schedules.append(clean_text)

        print(f"\n--- 【最終抽出結果: {tomorrow.strftime('%Y年%m月%d日')}】 ---")
        if tomorrow_schedules:
            for i, sch in enumerate(tomorrow_schedules, 1):
                print(f"【案件 {i}】\n内容: {sch}\n" + "-"*30)
        else:
            # 見つからなかった場合、どんな日付が並んでいるか1件だけサンプルを出す
            if items:
                sample = await items[0].inner_text()
                print(f"[DEBUG] 最初の要素のテキスト例: {' '.join(sample.split())[:100]}")
            print(f"！！対象日のスケジュールは見つかりませんでした。")

        await browser.close()
        print(f"\n=== 実行ログ終了 ===")

if __name__ == "__main__":
    asyncio.run(get_tomorrow_schedule())
