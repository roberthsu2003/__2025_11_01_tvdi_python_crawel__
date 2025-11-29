import os
from playwright.sync_api import sync_playwright

def get_html_path()-> str:
    """返回HTML文件的絕對路徑"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "waiting_demo.html")
    return f"file://{html_path}"

def demo_1_delayed_element(page):
    """示範等待延遲加載的元素出現"""
    #page.click("#trigger-delayed")  # 點擊按鈕觸發異步操作
    delay_button = page.locator("#trigger-delayed")  #取後Locator按鈕觸
    delay_button.click()  #發送點擊事件

    # 等待載入指示器出現
    page.wait_for_selector("#loading-1", state="visible")
    print("載入指示器已出現")

    # 等待載入指示器消失
    page.wait_for_selector("#loading-1", state="hidden")
    print("載入指示器已消失")

    page.wait_for_selector("div#delayed-result.result.show", state="visible")

    # 取得內容
    content = page.locator("#delayed-content").text_content()
    print(f"延遲加載的內容: {content}")

    

def main():
    path = get_html_path()
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False, slow_mo=500)

        # 打開新頁面
        page = browser.new_page()

        page.goto(path)

        
        page.wait_for_load_state("networkidle")  # 等待網絡空閒
        demo_1_delayed_element(page)
        browser.close()

if __name__ == "__main__":
    main()