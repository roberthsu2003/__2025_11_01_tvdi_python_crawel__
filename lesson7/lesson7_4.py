import json
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig,CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

dummy_html = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>電子商務產品目錄範例</title>
</head>
<body>
    <div class="category" data-cat-id="cat-001">
        <h2 class="category-name">3C電子產品</h2>
        
        <!-- 產品 1 -->
        <div class="product">
            <h3 class="product-name">無線藍牙耳機 Pro</h3>
            <p class="product-price">NT$ 2,980</p>
            
            <div class="product-details">
                <span class="brand">品牌: SoundMax</span>
                <span class="model">型號: SM-BT500</span>
            </div>
            
            <ul class="product-features">
                <li>主動降噪功能</li>
                <li>續航力30小時</li>
                <li>IPX7防水等級</li>
            </ul>
            
            <div class="review">
                <span class="reviewer">張先生</span>
                <span class="rating">★★★★☆ (4.5)</span>
                <p class="review-text">降噪效果非常好，長時間佩戴也很舒適</p>
            </div>
            
            <div class="review">
                <span class="reviewer">王小姐</span>
                <span class="rating">★★★★★ (5.0)</span>
                <p class="review-text">音質超出預期，CP值很高</p>
            </div>
        </div>
        
        <!-- 產品 2 -->
        <div class="product">
            <h3 class="product-name">智能運動手環</h3>
            <p class="product-price">NT$ 1,580</p>
            
            <div class="product-details">
                <span class="brand">品牌: FitLife</span>
                <span class="model">型號: FL-2023</span>
            </div>
            
            <ul class="product-features">
                <li>24小時心率監測</li>
                <li>睡眠品質分析</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

schema ={
    "name": "E-commerce 產品目錄",
    "baseSelector": "div.category",
    "fields":[
        {
            "name":"目錄名稱",
            "selector":"h2.category-name",
            "type":"text"
        },
        {
            "name":"產品列表",
            "selector":"div.product",
            # type: "nested_list" -> 用於提取一個物件列表。
            # 這裡我們有多個 <div class="product">，每個都代表一個產品物件。
            "type":"nested_list",
            "fields":[
                {
                    "name":"產品名稱",
                    "selector":"h3.product-name",
                    "type":"text"
                },
                {
                    "name":"價格",
                    "selector":"p.product-price",
                    "type":"text"
                },
                {
                    "name":"產品資訊",
                    "selector":"div.product-details",
                    # type: "nested" -> 用於提取單一的子物件。
                    # 每個產品只有一組 <div class="product-details">。
                    "type":"nested",
                    "fields":[
                        {
                            "name":"品牌",
                            "selector":"span.brand",
                            "type":"text"
                        },
                        {
                            "name":"型號",
                            "selector":"span.model",
                            "type":"text"
                        }
                    ]
                },
                {
                    "name":"功能列表",
                    "selector":"ul.product-features li",
                    # type: "list" -> 用於提取簡單的值列表。
                    # 我們只想獲取每個 <li> 的文字，組成一個陣列。
                    "type":"list",
                    "fields":[
                        {
                            "name":"功能",
                            "type":"text"
                        }
                    ]
                },
                {
                    "name":"評論",
                    "selector":"div.review",
                    # type: "nested_list" -> 再次使用，因為一個產品可以有多筆評論。
                    "type":"nested_list",
                    "fields":[
                        {
                            "name":"評論者",
                            "selector":"span.reviewer",
                            "type":"text"
                        },
                        {
                            "name":"評分",
                            "selector":"span.rating",
                            "type":"text"
                        },
                        {
                            "name":"內容",
                            "selector":"p.review-text",
                            "type":"text"
                        }
                    ]
                }
            ]
        }
    ]
}

async def extract_and_print_data():
    # 關鍵點:將 verbose 設為 False (或直接不寫),這樣提取的內容才會存入 result.extracted_content
    strategy = JsonCssExtractionStrategy(schema, verbose=False)
    
    config = CrawlerRunConfig(
        extraction_strategy=strategy,
        cache_mode=CacheMode.BYPASS
        
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"raw://{dummy_html}",            
            config=config
        )

        if not result.success:
            print(f"爬取失敗: {result.error_message}")
            return
        
        # 現在 result.extracted_content 會有內容了!
        print("--- 原始提取內容 (JSON 字串) ---")
        print(result.extracted_content)
        print("\n" + "="*40 + "\n")
        
        # 解析 JSON 字串並以美觀的格式印出
        if result.extracted_content:
            try:
                data = json.loads(result.extracted_content)
                print("--- 解析後的 JSON 物件 (美化格式) ---")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("錯誤:無法解析提取的內容為 JSON")
        else:
            print("沒有提取到任何內容。")

if __name__ == "__main__":
    asyncio.run(extract_and_print_data())