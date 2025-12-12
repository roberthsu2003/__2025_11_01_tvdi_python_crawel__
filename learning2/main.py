"""
台灣銀行匯率爬蟲 - 命令列版本

此程式每隔10分鐘自動抓取台灣銀行匯率資料並儲存為 JSON 檔案。
網址: https://rate.bot.com.tw/xrt?Lang=zh-TW
"""

import asyncio
from datetime import datetime
from crawler_module import ExchangeRateCrawler


async def main():
    """主程式：每隔10分鐘自動執行一次爬蟲"""
    print("=" * 60)
    print("🏦 台幣匯率爬蟲程式啟動...")
    print("=" * 60)
    print("📌 每10分鐘自動執行一次")
    print("📌 按 Ctrl+C 可停止程式\n")
    
    # 建立爬蟲實例
    crawler = ExchangeRateCrawler(verbose=True)
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'=' * 60}")
            print(f"▶ 第 {iteration} 次執行 ({current_time})")
            print(f"{'=' * 60}\n")
            
            # 抓取匯率資料
            result = await crawler.fetch_exchange_rates()
            
            if result['success']:
                print(f"✅ 成功抓取 {result['count']} 筆匯率資料")
                
                # 儲存為 JSON 檔案
                if result['data']:
                    filepath = crawler.save_to_json(result['data'])
                    print(f"💾 資料已儲存: {filepath}")
                
                # 顯示部分資料預覽
                print("\n📊 資料預覽（前5筆）:")
                print("-" * 60)
                for item in result['data'][:5]:
                    print(f"  {item.get('幣名', 'N/A'):15} | "
                          f"現金買入: {item.get('現金匯率_本行買入', '-'):8} | "
                          f"現金賣出: {item.get('現金匯率_本行賣出', '-'):8}")
                print("-" * 60)
            else:
                print(f"❌ 抓取失敗: {result.get('error', '未知錯誤')}")
            
            print(f"\n⏳ 等待10分鐘後再次執行...")
            print(f"   (下次執行時間約: {datetime.now().strftime('%H:%M')} + 10分鐘)\n")
            
            # 等待10分鐘 (600秒)
            await asyncio.sleep(600)
            
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("⛔ 程式被使用者中斷")
            print("=" * 60)
            break
        except Exception as e:
            print(f"\n❌ 執行過程中發生錯誤: {e}")
            print("⏳ 等待10分鐘後重試...")
            await asyncio.sleep(600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程式已結束")