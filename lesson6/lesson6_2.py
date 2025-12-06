import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    #建立一個AsyncWebCrawler的實體
    async with AsyncWebCrawler() as crawler:
        #Run the crawler on a URL
        result = await crawler.arun(url='https://www.bnext.com.tw/')
        print(type(result))
        #列印取出的結果
        #print(result.markdown)
        #print(result.cleaned_html)
        #print(result.raw_html)
        if result.success:            
            with open("output.md", "w", encoding="utf-8") as f:
                f.write(result.markdown)
            print("存檔成功!")
        else:
            print("失敗。")

#py檔執行
asyncio.run(main())
