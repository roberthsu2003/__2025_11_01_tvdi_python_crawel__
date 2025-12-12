"""
台灣銀行匯率爬蟲模組

此模組提供台灣銀行牌告匯率的爬蟲功能。
網址: https://rate.bot.com.tw/xrt?Lang=zh-TW
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


class ExchangeRateCrawler:
    """台灣銀行匯率爬蟲類別"""
    
    TARGET_URL = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
    
    # 定義爬蟲的 extraction schema
    SCHEMA = {
        "name": "台幣匯率",
        "baseSelector": "table[title='牌告匯率'] tr",
        "fields": [
            {
                "name": "幣名",
                "selector": "td[data-table='幣別'] div.visible-phone.print_hide",
                "type": "text"
            },
            {
                "name": "現金匯率_本行買入",
                "selector": '[data-table="本行現金買入"]',
                "type": "text"
            },
            {
                "name": "現金匯率_本行賣出",
                "selector": '[data-table="本行現金賣出"]',
                "type": "text"
            },
            {
                "name": "即期匯率_本行買入",
                "selector": '[data-table="本行即期買入"]',
                "type": "text"
            },
            {
                "name": "即期匯率_本行賣出",
                "selector": '[data-table="本行即期賣出"]',
                "type": "text"
            }
        ]
    }
    
    def __init__(self, verbose: bool = False):
        """
        初始化爬蟲
        
        Args:
            verbose: 是否啟用詳細日誌輸出
        """
        self.verbose = verbose
        self.last_fetch_time: Optional[datetime] = None
        self.last_data: Optional[List[Dict]] = None
    
    async def fetch_exchange_rates(self) -> Dict:
        """
        抓取台灣銀行匯率資料
        
        Returns:
            包含以下鍵值的字典:
            - success (bool): 是否成功抓取
            - data (List[Dict]): 匯率資料列表
            - count (int): 資料筆數
            - timestamp (str): 抓取時間
            - error (str): 錯誤訊息（如果有）
        """
        try:
            # 建立 extraction strategy
            extraction_strategy = JsonCssExtractionStrategy(
                self.SCHEMA, 
                verbose=self.verbose
            )
            
            # 設定爬蟲配置
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=extraction_strategy
            )
            
            # 執行爬蟲
            async with AsyncWebCrawler(verbose=self.verbose) as crawler:
                result = await crawler.arun(
                    url=self.TARGET_URL,
                    config=config
                )
                
                if not result.success:
                    return {
                        'success': False,
                        'data': [],
                        'count': 0,
                        'timestamp': datetime.now().isoformat(),
                        'error': result.error_message
                    }
                
                # 解析資料
                data = json.loads(result.extracted_content)
                self.last_data = data
                self.last_fetch_time = datetime.now()
                
                if self.verbose:
                    print(f"成功抓取 {len(data)} 筆匯率資料")
                
                return {
                    'success': True,
                    'data': data,
                    'count': len(data),
                    'timestamp': self.last_fetch_time.isoformat(),
                    'error': None
                }
                
        except Exception as e:
            error_msg = f"抓取資料時發生錯誤: {str(e)}"
            if self.verbose:
                print(error_msg)
            return {
                'success': False,
                'data': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'error': error_msg
            }
    
    def save_to_json(self, data: List[Dict], directory: str = "data") -> str:
        """
        儲存匯率資料為 JSON 檔案
        
        Args:
            data: 要儲存的匯率資料
            directory: 儲存目錄
            
        Returns:
            儲存的檔案路徑
        """
        # 確保資料夾存在
        os.makedirs(directory, exist_ok=True)
        
        # 建立基於時間的檔案名稱
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"台幣匯率_{timestamp}.json"
        filepath = os.path.join(directory, filename)
        
        # 儲存 JSON 檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"資料已儲存至: {filepath}")
        
        return filepath
    
    def get_last_fetch_info(self) -> Dict:
        """
        取得最後一次抓取的資訊
        
        Returns:
            包含最後抓取時間和資料筆數的字典
        """
        return {
            'last_fetch_time': self.last_fetch_time,
            'data_count': len(self.last_data) if self.last_data else 0,
            'has_data': self.last_data is not None
        }


# 提供簡單的函數介面供不想使用類別的使用者
async def get_exchange_rates(verbose: bool = False) -> Dict:
    """
    簡單的函數介面來抓取匯率資料
    
    Args:
        verbose: 是否啟用詳細日誌輸出
        
    Returns:
        包含匯率資料的字典
    """
    crawler = ExchangeRateCrawler(verbose=verbose)
    return await crawler.fetch_exchange_rates()
