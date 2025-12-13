import asyncio,json
from crawl4ai import AsyncWebCrawler,CrawlerRunConfig,CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    html = """
<div class="item">
    <h2>項目1</h2>
    <a href="https://example.com/item1">連結1</a>
</div>"""

    schema ={
        "name":"項目名稱",
        "baseSelector":"div.item",
        "fields":[
            {
                "name":"標題",
                "selector":"h2",
                "type":"text"
            },
            {
                "name":"連結名稱",
                "selector":"a",
                "type":"text"
            },
            {
                "name":"連結網址",
                "selector":"a",
                "type":"attribute",
                "attribute":"href"
            }
        ]
    }

    strategy = JsonCssExtractionStrategy(schema)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=strategy
        )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"raw://{html}",
            config=run_config)
        data = json.loads(result.extracted_content)
        for item in data:
            print(f"標題: {item['標題']}")
            print(f"連結名稱: {item['連結名稱']}")
            print(f"連結網址: {item['連結網址']}")

if __name__ == "__main__":
    asyncio.run(main())