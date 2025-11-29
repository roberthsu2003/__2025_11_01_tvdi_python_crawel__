import os
from playwright.sync_api import sync_playwright



def main():
    path = "https://www.thsrc.com.tw/"
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False, slow_mo=500)

        # 打開新頁面
        page = browser.new_page()

        page.goto(path)

        
        page.wait_for_load_state("domcontentloaded")  # 等待網絡空閒
        page.wait_for_timeout(3000)  # 等待3秒以觀察效果

        browser.close()

if __name__ == "__main__":
    main()