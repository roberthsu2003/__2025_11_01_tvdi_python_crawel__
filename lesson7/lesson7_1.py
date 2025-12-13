import asyncio
from crawl4ai import AsyncWebCrawler,CrawlerRunConfig,CacheMode

async def main():
    html = """
<div class="item>
    <h2>項目10</h2>
    <a href="https://example.com/item1">連結1</a>
    abc
</div>"""
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config)

if __name__ == "__main__":
    asyncio.run(main())