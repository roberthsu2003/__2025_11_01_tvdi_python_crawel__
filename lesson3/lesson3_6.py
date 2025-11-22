from playwright.sync_api import sync_playwright
from time import sleep

def main():
    with sync_playwright() as p:
        print(f"p={type(p)}")
        # 啟動瀏覽器
        browser = p.webkit.launch(headless=False)
        
        print(f"browser:{type(browser)}")
        # 開啟新分頁
        page = browser.new_page()

        print(f"page:{type(page)}")
        
        # 訪問網站
        page.goto("https://www.google.com")
        
        # 取得標題
        print(page.title())

        sleep(20)
        
        # 關閉瀏覽器
        browser.close()

if __name__ == "__main__":
    main()