import asyncio,json
from crawl4ai import AsyncWebCrawler,CrawlerRunConfig,CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # 模擬加密貨幣網頁
    html = """
    <html>
      <body>
        <div class='crypto-row'>
          <h2 class='coin-name'>比特幣</h2>
          <span class='coin-price'>$28,000</span>
        </div>
        <div class='crypto-row'>
          <h2 class='coin-name'>以太幣</h2>
          <span class='coin-price'>$1,800</span>
        </div>
      </body>
    </html>
    """

    schema ={
        "name":"加密貨幣列表",
        "baseSelector":"body",
        "fields":[
            {
                "name":"加密貨幣",
                "selector":"div.crypto-row",
                "type":"list",
                "fields":[
                    {
                        "name":"加密貨幣名",
                        "selector":"h2.coin-name",
                        "type":"text"
                    },
                    {
                        "name":"價格",
                        "selector":"span.coin-price",
                        "type":"text"
                    }
                ] 
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
        print(data)
        
        # for item in data:
        #     print(f"幣名: {item['加密貨幣名']}")
        #     print(f"價格: {item['價格']}")
        #     print("=============")
        

if __name__ == "__main__":
    asyncio.run(main())