import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    """
    非同步主要函數，用於配置和初始化 AsyncWebCrawler。
    此函數設定瀏覽器配置選項，包括無頭模式和隱私模式，
    然後在非同步上下文管理器中建立 AsyncWebCrawler 的實例。
    """
    # 配置瀏覽器選項
    browser_config = BrowserConfig(
        headless=False  # 設定為非無頭模式，瀏覽器界面將可見
        )
    
# 配置CrawlerRunConfig選項
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS  # 設定為繞過快取模式
        )
    
    #建立一個AsyncWebCrawler的實體
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='http://example.com',
            config=run_config)
        

    print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())