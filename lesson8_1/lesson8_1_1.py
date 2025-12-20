import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    url = 'https://www.wantgoo.com/stock/2330/technical-chart'

    browserConfig = BrowserConfig(
        headless=True,
    )

    crawlerRunConfig = CrawlerRunConfig(
        cache_mode = CacheMode.BYPASS,
        scan_full_page=True,
        verbose=True
    )

    async with AsyncWebCrawler(config=browserConfig) as crawler:
        result = await crawler.arun(            
            url = url,
            config = crawlerRunConfig
        )

        if result.success:
            print("下載成功")
            print(result.markdown)
        else:
            print("下載失敗")

if __name__ == "__main__":
    asyncio.run(main())