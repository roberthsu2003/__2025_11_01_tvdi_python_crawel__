import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from pprint import pprint


async def main():
    # 模擬電子商務網頁
    html = """
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

    # 修正後的 schema：使用 nested_list 處理評論
    schema = {
        "name": "產品",
        "baseSelector": ".product",
        "fields": [
            {
                "name": "產品名稱",
                "selector": ".product-name",
                "type": "text"
            },
            {
                "name": "價格",
                "selector": ".product-price",
                "type": "text"
            },
            {
                "name": "品牌",
                "selector": ".brand",
                "type": "text"
            },
            {
                "name": "型號",
                "selector": ".model",
                "type": "text"
            },
            {
                "name": "特徵",
                "selector": ".product-features li",
                "type": "list",
                "fields": [
                    {"name": "內容", "type": "text"}
                ]
            },
            {
                "name": "評論",
                "selector": ".review",
                "type": "nested_list",
                "fields": [
                    {
                        "name": "評論者",
                        "selector": ".reviewer",
                        "type": "text"
                    },
                    {
                        "name": "評分",
                        "selector": ".rating",
                        "type": "text"
                    },
                    {
                        "name": "評論內容",
                        "selector": ".review-text",
                        "type": "text"
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
            config=run_config
        )
        data = json.loads(result.extracted_content)
        

        if isinstance(data, list):
            for product in data:
                print(f"產品名稱: {product.get('產品名稱', 'N/A')}")
                print(f"價格: {product.get('價格', 'N/A')}")
                print(f"品牌: {product.get('品牌', 'N/A')}")
                print(f"型號: {product.get('型號', 'N/A')}")

                # 處理特徵
                features = product.get('特徵', [])
                if features:
                    if isinstance(features, list):
                        # 如果是 list 型態，提取每個特徵的內容
                        feature_texts = []
                        for f in features:
                            if isinstance(f, dict):
                                feature_texts.append(f.get('內容', ''))
                            else:
                                feature_texts.append(str(f))
                        print(f"特徵: {', '.join(feature_texts)}")
                    else:
                        print(f"特徵: {features}")

                # 處理評論（使用 nested_list 結構）
                reviews = product.get('評論', [])
                if reviews:
                    print("評論:")
                    if isinstance(reviews, list):
                        for review in reviews:
                            if isinstance(review, dict):
                                reviewer = review.get('評論者', 'N/A')
                                rating = review.get('評分', 'N/A')
                                text = review.get('評論內容', 'N/A')
                                print(f"  - {reviewer} {rating}: {text}")
                    else:
                        print(f"  - {reviews}")

                print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())