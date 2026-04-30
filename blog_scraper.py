from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta, timezone
import time

URL = "https://web.familyclub.jp/"

def get_yesterday_string():
    # サーバー(GitHub Actions)環境を考慮し、JST(日本標準時)を明示的に指定
    JST = timezone(timedelta(hours=+9), 'JST')
    y = datetime.now(JST) - timedelta(days=1)
    return y.strftime("%Y.%m.%d")

def scroll_until_found(page, target):
    print(f"{target} が出るまでスクロール")
    last_height = 0
    for _ in range(30):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.2)
        text = page.inner_text("body")
        if target in text:
            print("昨日を検出 → 即停止")
            return
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            print("これ以上読み込めない → 停止")
            return
        last_height = new_height

def extract_text(page):
    page.evaluate("""
        document.querySelectorAll('header, footer, nav, aside').forEach(el => el.remove());
    """)
    return page.inner_text("body")

def cut_until_yesterday(text, yesterday):
    if yesterday in text:
        return text.split(yesterday)[0] + yesterday
    return text

def run_scraper():
    """main.pyから呼び出されるメイン関数。取得したテキストを返す。"""
    yesterday = get_yesterday_string()
    
    with sync_playwright() as p:
        # サーバー上で動かすため headless=True に変更
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        scroll_until_found(page, yesterday)
        text = extract_text(page)
        browser.close()

    final_text = cut_until_yesterday(text, yesterday)
    return final_text

if __name__ == "__main__":
    # 単独テスト用
    result = run_scraper()
    print(result[:100] + "...") # 最初の100文字だけ表示
