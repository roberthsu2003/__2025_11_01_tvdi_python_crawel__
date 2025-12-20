
import asyncio,json
from crawl4ai import AsyncWebCrawler,CrawlerRunConfig,CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from pprint import pprint

async def main():
    
    schema ={
        "name":"匯率資訊",
        "baseSelector":"table[title='牌告匯率'] tr",
        "fields":[
            {
                "name":"幣別",
                "selector":"td[data-table='幣別'] div.print_show",
                "type":"text"
            },
            {
                "name":"本行即期買入",
                "selector":"td[data-table='本行即期買入']",
                "type":"text"
            },
            {
                "name":"本行即期賣出",
                "selector":"td[data-table='本行即期賣出']",
                "type":"text"
            }
            
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema)

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy
        )
    async with AsyncWebCrawler() as crawler:
        url='https://rate.bot.com.tw/xrt?Lang=zh-TW'
        result = await crawler.arun(
            url=url,
            config=run_config)
        data = json.loads(result.extracted_content)
        pprint(data)
        

if __name__ == "__main__":
    asyncio.run(main())