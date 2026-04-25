import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

async def get_tomorrow_schedule():
    async with async_playwright() as p:
        # 1. 日付の計算
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        url_ym = tomorrow.strftime("%Y%m")
        # サイトの表記に合わせて "05.01" 形式にする
        search_date = tomorrow.strftime("%m.%d")
        
        print(f"=== 実行ログ開始: {now.strftime('%Y-%m-%d %H:%M:%S')} ===")
        print(f"検索対象日: {search_date}")
        
        # 2. ブラウザ起動
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://jr-official.starto.jp/s/jr/media/list?dy={url_ym}"
        print(f"アクセス中: {url}")
        
        await page.goto(url, wait_until="networkidle")

        # 3. スケジュール要素の取得
        # ジュニア公式サイトのリストアイテムを全取得
        items = await page.query_selector_all(".p-media-list__item")
        
        print(f"ページ内の項目数: {len(items)} 件をスキャン中...\n")
        
        tomorrow_schedules = []
        
        for i, item in enumerate(items):
            # 要素内の全テキストを取得
            text = await item.inner_text()
            clean_text = " ".join(text.split()) # 余計な改行や空白を整理
            
            # ログ表示：すべての項目の中身を一度表示（デバッグ用）
            # print(f"  [Check {i+1}] {clean_text[:50]}...") 

            # 明日の日付が含まれているか判定
            if search_date in text:
                print(f"  → ★一致確認: {search_date} のデータを見つけました")
                tomorrow_schedules.append(clean_text)

        # 4. 結果の出力
        print(f"\n--- 【最終抽出結果: {tomorrow.strftime('%Y年%m月%d日')}】 ---")
        
        if tomorrow_schedules:
            for i, sch in enumerate(tomorrow_schedules, 1):
                # ここで抽出した文章の全文をログに表示します
                print(f"【案件 {i}】")
                print(f"内容: {sch}")
                print("-" * 50)
                
                # 特定ワードの通知テスト
                target_word = "特定ワード" # ここを書き換えてください
                if target_word in sch:
                    print(f"！！【通知対象】「{target_word}」が含まれています！！")
        else:
            print(f"！！警告！！ {search_date} のスケジュールは抽出されませんでした。")
            print("※サイト上の日付形式が '5.1' のように0埋めなしの可能性があります。")

        await browser.close()
        print(f"\n=== 実行ログ終了 ===")

if __name__ == "__main__":
    asyncio.run(get_tomorrow_schedule())
