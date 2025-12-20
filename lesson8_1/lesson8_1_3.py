import asyncio
import json
from typing import Dict, List, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


def get_stock_schema() -> Dict:
    """
    取得股票資訊的 CSS 提取 Schema
    
    Returns:
        股票資訊的 Schema 定義
    """
    return {
        "name": "StockInfo",
        "baseSelector": "main.main",
        "fields": [
            {
                "name": "日期時間",
                "selector": "time.last-time#lastQuoteTime",
                "type": "text"
            },
            {
                "name": "股票號碼",
                "selector": "span.astock-code[c-model='id']",
                "type": "text"
            },
            {
                "name": "股票名稱",
                "selector": "h3.astock-name[c-model='name']",
                "type": "text"
            },
            {
                "name": "即時價格",
                "selector": "div.quotes-info div.deal",
                "type": "text"
            },
            {
                "name": "漲跌",
                "selector": "div.quotes-info span.chg[c-model='change']",
                "type": "text"
            },
            {
                "name": "漲跌百分比",
                "selector": "div.quotes-info span.chg-rate[c-model='changeRate']",
                "type": "text"
            },
            {
                "name": "開盤價",
                "selector": "div.quotes-info #quotesUl span[c-model-dazzle='text:open,class:openUpDn']",
                "type": "text"
            },
            {
                "name": "最高價",
                "selector": "div.quotes-info #quotesUl span[c-model-dazzle='text:high,class:highUpDn']",
                "type": "text"
            },
            {
                "name": "成交量(張)",
                "selector": "div.quotes-info #quotesUl span[c-model='volume']",
                "type": "text"
            },
            {
                "name": "最低價",
                "selector": "div.quotes-info #quotesUl span[c-model-dazzle='text:low,class:lowUpDn']",
                "type": "text"
            },
            {
                "name": "前一日收盤價",
                "selector": "div.quotes-info #quotesUl span[c-model='previousClose']",
                "type": "text"
            }
        ]
    }


async def fetch_stock_info(
    crawler: AsyncWebCrawler, 
    stock_code: str, 
    base_config: CrawlerRunConfig,
    semaphore: asyncio.Semaphore
) -> Optional[Dict]:
    """
    抓取單一股票資訊
    
    Args:
        crawler: AsyncWebCrawler 實例
        stock_code: 股票代碼
        base_config: 基礎爬蟲執行設定
        semaphore: 用於限制並行數量的信號量
    
    Returns:
        股票資訊字典，失敗時返回 None
    """
    async with semaphore:  # 限制並行數量
        url = f'https://www.wantgoo.com/stock/{stock_code}/technical-chart'
        
        try:
            # 針對每個股票創建帶有等待條件的配置
            # 等待關鍵元素載入完成，確保動態內容已經渲染
            config = CrawlerRunConfig(
                cache_mode=base_config.cache_mode,
                extraction_strategy=base_config.extraction_strategy,
                scan_full_page=base_config.scan_full_page,
                verbose=base_config.verbose,
                # 等待多個關鍵元素載入完成
                wait_for="js:() => document.querySelector('div.quotes-info div.deal') && document.querySelector('span.astock-code[c-model=\"id\"]') && document.querySelector('#quotesUl span[c-model=\"volume\"]')",
                wait_for_timeout=15000,  # 15 秒超時
                page_timeout=30000  # 整體頁面載入 30 秒超時
            )
            
            result = await crawler.arun(url=url, config=config)
            
            if result.success:
                print(f"✓ 股票 {stock_code} 下載成功")
                return {
                    "stock_code": stock_code,
                    "data": result.extracted_content
                }
            else:
                print(f"✗ 股票 {stock_code} 下載失敗")
                return None
                
        except Exception as e:
            print(f"✗ 股票 {stock_code} 發生錯誤: {e}")
            return None


async def main():
    """主程式：並行爬取多個股票資訊"""
    stock_codes = ["2330", "2317", "2454", "2412", "2308"]
    
    # 建立 Schema 和配置
    stock_schema = get_stock_schema()
    extraction_strategy = JsonCssExtractionStrategy(schema=stock_schema)
    
    browser_config = BrowserConfig(headless=True)
    
    # 建立基礎配置（wait_for 會在 fetch_stock_info 中針對每個請求設定）
    base_crawler_run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
        scan_full_page=True,
        verbose=False  # 關閉詳細輸出，使用自訂的輸出訊息
    )
    
    # 限制同時爬取的數量（避免對目標網站造成過大負擔）
    # 降低並行數量，給每個請求更多時間等待動態內容載入
    semaphore = asyncio.Semaphore(3)
    
    print("開始爬取股票資訊，等待動態內容載入完成...\n")
    
    # 使用單一 crawler 實例並行爬取所有股票
    async with AsyncWebCrawler(config=browser_config) as crawler:
        tasks = [
            fetch_stock_info(crawler, code, base_crawler_run_config, semaphore)
            for code in stock_codes
        ]
        
        # 並行執行所有任務
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        print("\n" + "=" * 50)
        print("爬取結果摘要")
        print("=" * 50)
        
        successful_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"發生異常: {result}")
            elif result is not None:
                successful_results.append(result)
                print(f"\n股票代碼: {result['stock_code']}")
                print(result['data'])
                print("-" * 50)
        
        print(f"\n總計: 成功 {len(successful_results)}/{len(stock_codes)} 筆")


if __name__ == "__main__":
    asyncio.run(main())