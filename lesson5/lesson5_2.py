import os
from playwright.sync_api import sync_playwright

def get_news(page):
    lis = page.locator("ul#alltype-news.news-list > li").all()
    print(type(lis))
    print(f"共找到 {len(lis)} 筆最新消息")
    for item in lis:
        date = item.locator("div.news-date").text_content()
        title = item.locator("div.news-title").text_content()
        print(date)
        print(title)
        print("=" * 60)

def schedule_and_fare(page):
    page.locator('#select_location01').select_option("台北")
    page.locator('#select_location02').select_option("台南")



def main():
    path = "https://www.thsrc.com.tw/"
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False, slow_mo=500)

        # 打開新頁面
        page = browser.new_page()

        page.goto(path)

        
        page.wait_for_load_state("domcontentloaded")  # 等待網絡空閒
        page.locator("button",has_text="我同意").click()  # 點擊按鈕觸發異步操作
        get_news(page)       
        schedule_and_fare(page)

        page.wait_for_timeout(3000)  # 等待3秒以觀察效果

        browser.close()

if __name__ == "__main__":
    main()