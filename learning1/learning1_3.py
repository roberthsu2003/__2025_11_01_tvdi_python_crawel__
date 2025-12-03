import time
import asyncio

async def download_file_async(file_name):
    print(f"開始下載{file_name}...")
    await asyncio.sleep(2)
    print(f"{file_name}下載完成")
    return f"{file_name}_data"

async def main_async():
    start = time.time()

    result = await asyncio.gather(
        download_file_async("檔案A.pdf"),
        download_file_async("檔案B.pdf"),
        download_file_async("檔案C.pdf")
    )

    end = time.time()
    print(f"\n總耗時:{end - start:.2f}秒")

asyncio.run(main_async())