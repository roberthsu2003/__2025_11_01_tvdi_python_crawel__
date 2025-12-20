import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    stock_codes = ["2330","2317","2454","2412","2308"]
    for code in stock_codes:
        url = f'https://www.wantgoo.com/stock/{code}/technical-chart'

        # 定義 CSS 提取 Schema
        # 根據網頁結構，我們需要找到包含股票資訊的區塊
        # 這裡假設股票名稱在 .stock-name 類別中，即時價格在 .stock-price 類別中
        # 實際應用中需要根據目標網站的 HTML 結構來調整這些選擇器
        stock_schema = {
            "name": "StockInfo",
            "baseSelector": "main.main",  # 從整個頁面開始選擇
            "fields": [
                {
                    "name":"日期時間",
                    "selector":"time.last-time#lastQuoteTime",
                    "type":"text"
                },
                {
                    "name": "股票號碼",
                    "selector": "span.astock-code[c-model='id']", # 假設股票代碼在這個選擇器下
                    "type": "text"
                },
                {
                    "name": "股票名稱",
                    "selector": "h3.astock-name[c-model='name']",  # 假設股票名稱在這個選擇器下
                    "type": "text"
                },
                {
                    "name": "即時價格",
                    "selector":"div.quotes-info div.deal",
                    "type": "text"

                },
                {
                    "name": "漲跌",
                    "selector":"div.quotes-info span.chg[c-model='change']",
                    "type": "text"
                },
                {
                    "name": "漲跌百分比",
                    "selector":"div.quotes-info span.chg-rate[c-model='changeRate']",
                    "type": "text"
                },
                {
                    "name": "開盤價",
                    "selector":"div.quotes-info #quotesUl span[c-model-dazzle='text:open,class:openUpDn']",
                    "type": "text"
                },
                {
                    "name": "最高價",
                    "selector":"div.quotes-info #quotesUl span[c-model-dazzle='text:high,class:highUpDn']",
                    "type": "text"

                },
                {
                    "name": "成交量(張)",
                    "selector":"div.quotes-info #quotesUl span[c-model='volume']",
                    "type": "text" 
                },
                {
                    "name": "最低價",
                    "selector":"div.quotes-info #quotesUl span[c-model-dazzle='text:low,class:lowUpDn']",
                    "type": "text" 
                },
                {
                    "name": "前一日收盤價",
                    "selector":"div.quotes-info #quotesUl span[c-model='previousClose']",
                    "type": "text" 
                }

            ]
        }

        extraction_strategy = JsonCssExtractionStrategy(schema=stock_schema)

        browserConfig = BrowserConfig(
            headless=True,
        )

        crawlerRunConfig = CrawlerRunConfig(
            cache_mode = CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
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
                print(result.extracted_content)
                print("==========================")
            else:
                print("下載失敗")

if __name__ == "__main__":
    asyncio.run(main())