import os
from playwright.sync_api import sync_playwright

def get_html_path()-> str:
    """返回HTML文件的絕對路徑"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "waiting_demo.html")
    return f"file://{html_path}"

def main():
    path = get_html_path()
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False, slow_mo=500)

        # 打開新頁面
        page = browser.new_page()

        page.goto(path)

        
        page.wait_for_load_state("networkidle")  # 等待網絡空閒
        page.click("#trigger-delayed")  # 點擊按鈕觸發異步操作
        page.wait_for_timeout(3000)  # 等待3秒以觀察效果


        browser.close()

if __name__ == "__main__":
    main()