from playwright.sync_api import sync_playwright
import os
from time import sleep

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,slow_mo=500)
        page = browser.new_page()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_file = os.path.join(current_dir,"form_demo.html")
        #print(f"file://{html_file}")
        page.goto(f"file://{html_file}")
        page.fill("input#name","張三")
        page.fill("input#email","zhang@example.com")
        page.select_option("select#country","Taiwan")
        page.check("input#subscribe")
        sleep(3)
        browser.close()


if __name__ == "__main__":
    main()