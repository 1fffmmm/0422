import os
from playwright.sync_api import sync_playwright
# notifier.pyから通知関数をインポート
from notifier import check_keywords_and_notify

# 環境変数から取得するように変更（GitHub Secretsで管理）
AUTH_TOKEN = os.environ.get("X_AUTH_TOKEN")

def run_scraper_and_notify():
    if not AUTH_TOKEN:
        print("【エラー】 X_AUTH_TOKEN が環境変数に設定されていません。")
        return

    with sync_playwright() as p:
        # GitHub Actions（サーバー）上で動かすためheadless=Trueは必須
        browser = p.chromium.launch(headless=True)
        
        # User-AgentはMacのChromeを装う設定を維持
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        context.add_cookies([{
            "name": "auth_token",
            "value": AUTH_TOKEN,
            "domain": ".x.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }])

        page = context.new_page()
        page.set_default_timeout(60000)

        url = "https://x.com/search?q=from%3Ajr_official_X%20within_time%3A24h&f=live"
        
        try:
            print("𝕏へアクセスを開始します...")
            page.goto(url, wait_until="domcontentloaded") 
            
            print("初期コンテンツの読み込みを待機中...")
            page.wait_for_timeout(5000)
            
            print("ポストを全件読み込むためにスクロール中...")
            for i in range(3):
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(1500)
            
            page.wait_for_selector('article div[data-testid="tweetText"]', timeout=30000)
            tweets = page.query_selector_all('article div[data-testid="tweetText"]')
            
            results = []
            for t in tweets:
                text = t.inner_text().replace('\n', ' ').strip()
                if text and text not in results:
                    results.append(text)

            if results:
                print(f"【成功】 {len(results)}件のポストを取得しました。通知処理へ移行します。")
                # 取得したリストを1つの文字列に結合
                content_text = "\n---\n".join(results)
                
                # ドライブを介さず、直接notifierの関数へ渡す
                check_keywords_and_notify(content_text, source="tweet")
            else:
                print("【確認】 検索結果にポストが見つかりませんでした。")
                
        except Exception as e:
            print(f"【エラー】 発生しました: {e}")
            # ※GitHub Actions上ではスクリーンショットを保存しても終了後に消えるため、
            # アーティファクトとしてアップロードする設定にしない限り確認はできません。
            
        finally:
            browser.close()

if __name__ == "__main__":
    run_scraper_and_notify()
    
