# Python Web Crawling Course - Copilot Instructions

## 專案概述
這是一個 Python 網頁爬蟲教學專案，包含多個課程章節和實作範例。

## 程式碼風格
- 使用 Python 3.x
- 遵循 PEP 8 編碼規範
- 優先使用 type hints 提高代碼可讀性
- 函數和類別必須包含 docstrings
- 變數命名使用有意義的英文名稱

## 專案結構
- `lessonX/` - 各課程章節目錄
  - `.ipynb` - Jupyter Notebook 教學檔案
  - `.py` - Python 腳本檔案
- `link/` - 相關連結和資源
- `.github/` - GitHub 相關設定

## 技術棧
- **網頁爬蟲**: requests
- **crawl4ai (v0.7.7)**
- **資料處理**: pandas, numpy
- **開發工具**: Jupyter Notebook

## Crawl4AI 專用指示 ⚠️ 重要
- **版本**: 必須使用 crawl4ai v0.7.7
- **文檔查詢**: 當使用 crawl4ai 相關功能時，**必須先使用 MCP Context7 工具查詢最新文檔**
  - 使用 `mcp_context7_resolve-library-id` 工具解析 crawl4ai 庫 ID
  - 使用 `mcp_context7_get-library-docs` 工具獲取 v0.7.7 的文檔和範例
- **開發流程**:
  1. 先查詢 Context7 獲取 crawl4ai v0.7.7 的最新用法
  2. 根據官方文檔提供程式碼建議
  3. 確保使用的 API 和方法與 v0.7.7 相容

## 編碼準則

### 爬蟲開發
- 遵守 robots.txt 規範
- 加入適當的延遲，避免對目標網站造成負擔
- 使用 try-except 處理網路請求例外
- 記錄爬取的資料來源和時間

### 資料處理
- 清理和驗證爬取的資料
- 使用 pandas 進行結構化資料處理
- 適當處理缺失值和異常值

### 錯誤處理
- 使用明確的例外處理
- 記錄錯誤訊息以便除錯
- 網路請求應包含重試機制

### 程式碼組織
- 將重複使用的功能封裝成函數
- 複雜的爬蟲邏輯應模組化
- 設定檔和敏感資訊應外部化

## 範例程式碼格式

```python
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict

def fetch_webpage(url: str, timeout: int = 10) -> Optional[str]:
    """
    抓取網頁內容
    
    Args:
        url: 目標網址
        timeout: 逾時時間（秒）
    
    Returns:
        網頁 HTML 內容，失敗時返回 None
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
```

## 注意事項
- Jupyter Notebook 中的程式碼應該可以獨立執行
- 提供清晰的註解說明爬蟲邏輯
- 範例應該具有教學意義，易於理解
- 考慮網路環境的穩定性，加入適當的錯誤處理
