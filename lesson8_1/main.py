"""
股票即時監控桌面應用程式

使用 Tkinter 建立 GUI，結合 crawl4ai 爬蟲技術，
提供台灣股市即時資訊監控功能。

Author: Created on 2025-12-20
"""

import asyncio
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Optional, Set
from datetime import datetime
import threading
import queue
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import twstock


# ==================== 爬蟲模組 ====================

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


async def fetch_single_stock(
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
    async with semaphore:
        url = f'https://www.wantgoo.com/stock/{stock_code}/technical-chart'
        
        try:
            # 針對每個股票創建帶有等待條件的配置
            config = CrawlerRunConfig(
                cache_mode=base_config.cache_mode,
                extraction_strategy=base_config.extraction_strategy,
                scan_full_page=base_config.scan_full_page,
                verbose=base_config.verbose,
                # 等待關鍵元素載入完成
                wait_for="js:() => document.querySelector('div.quotes-info div.deal') && document.querySelector('span.astock-code[c-model=\"id\"]') && document.querySelector('#quotesUl span[c-model=\"volume\"]')",
                wait_for_timeout=15000,
                page_timeout=30000
            )
            
            result = await crawler.arun(url=url, config=config)
            
            if result.success and result.extracted_content:
                try:
                    data = json.loads(result.extracted_content)
                    if data and len(data) > 0:
                        stock_data = data[0]
                        stock_data['stock_code'] = stock_code
                        stock_data['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        return stock_data
                except json.JSONDecodeError:
                    print(f"✗ 股票 {stock_code} JSON 解析失敗")
                    return None
            else:
                print(f"✗ 股票 {stock_code} 下載失敗")
                return None
                
        except Exception as e:
            print(f"✗ 股票 {stock_code} 發生錯誤: {e}")
            return None


async def fetch_multiple_stocks(stock_codes: List[str]) -> List[Dict]:
    """
    批次並行爬取多支股票資訊
    
    Args:
        stock_codes: 股票代碼列表
    
    Returns:
        成功爬取的股票資訊列表
    """
    stock_schema = get_stock_schema()
    extraction_strategy = JsonCssExtractionStrategy(schema=stock_schema)
    
    browser_config = BrowserConfig(headless=True)
    
    base_crawler_run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
        scan_full_page=True,
        verbose=False
    )
    
    # 限制同時爬取數量
    semaphore = asyncio.Semaphore(3)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        tasks = [
            fetch_single_stock(crawler, code, base_crawler_run_config, semaphore)
            for code in stock_codes
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 過濾成功的結果
        successful_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"發生異常: {result}")
            elif result is not None:
                successful_results.append(result)
        
        return successful_results


def run_crawler_in_thread(stock_codes: List[str], result_queue: queue.Queue):
    """
    在背景執行緒中執行爬蟲任務
    
    Args:
        stock_codes: 要爬取的股票代碼列表
        result_queue: 用於傳遞結果的佇列
    """
    try:
        # 在執行緒中建立新的事件迴圈
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(fetch_multiple_stocks(stock_codes))
        result_queue.put(('success', results))
        
        loop.close()
    except Exception as e:
        result_queue.put(('error', str(e)))


# ==================== GUI 主程式 ====================

class StockMonitorApp:
    """股票監控應用程式主類別"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化應用程式
        
        Args:
            root: Tkinter 根視窗
        """
        self.root = root
        self.root.title("台灣股市即時監控系統")
        self.root.geometry("1200x700")
        
        # 觀察清單（使用 Set 避免重複）
        self.watchlist: Set[str] = set()
        
        # 股票資料快取
        self.stock_data_cache: Dict[str, Dict] = {}
        
        # 自動更新相關
        self.auto_update_enabled = False
        self.update_timer_id = None
        self.is_updating = False
        
        # 爬蟲結果佇列
        self.result_queue = queue.Queue()
        
        # 建立 UI
        self.setup_ui()
        
        # 載入台灣股票清單
        self.load_tw_stocks()
        
        # 綁定視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 開始檢查佇列
        self.check_queue()
    
    def setup_ui(self):
        """建立使用者介面"""
        # TODO: Phase 3 - 實作 UI 佈局
        
        # 主要容器 - 使用 PanedWindow 分割左右面板
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左側面板 - 股票選擇區
        self.setup_left_panel(main_paned)
        
        # 右側面板 - 資料顯示區
        self.setup_right_panel(main_paned)
        
        # 頂部工具列
        self.setup_toolbar()
    
    def setup_toolbar(self):
        """建立頂部工具列"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # 手動更新按鈕
        self.update_btn = ttk.Button(
            toolbar,
            text="🔄 手動更新",
            command=self.manual_update,
            state=tk.NORMAL
        )
        self.update_btn.pack(side=tk.LEFT, padx=5)
        
        # 自動更新開關
        self.auto_update_var = tk.BooleanVar(value=False)
        auto_update_check = ttk.Checkbutton(
            toolbar,
            text="自動更新 (每分鐘)",
            variable=self.auto_update_var,
            command=self.toggle_auto_update
        )
        auto_update_check.pack(side=tk.LEFT, padx=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(toolbar, text="就緒")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 最後更新時間
        self.last_update_label = ttk.Label(toolbar, text="")
        self.last_update_label.pack(side=tk.RIGHT, padx=5)
    
    def setup_left_panel(self, parent):
        """建立左側股票選擇面板"""
        # TODO: Phase 4 - 實作左側面板
        left_frame = ttk.Frame(parent, width=280)
        parent.add(left_frame, weight=1)
        
        # 標題
        title_label = ttk.Label(
            left_frame,
            text="📈 台灣股票清單",
            font=('Arial', 18, 'bold')
        )
        title_label.pack(pady=10)
        
        # 搜尋框（增強版）
        search_frame = ttk.LabelFrame(
            left_frame,
            text="  搜尋股票  ",
            padding=12,
            style='Large.TLabelframe'
        )
        
        # 設定 LabelFrame 標題字體
        style = ttk.Style()
        style.configure('Large.TLabelframe', font=('Arial', 14, 'bold'))
        style.configure('Large.TLabelframe.Label', font=('Arial', 14, 'bold'))
        
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X)
        
        ttk.Label(
            search_input_frame,
            text="🔍",
            font=('Arial', 18)
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = ttk.Entry(
            search_input_frame,
            textvariable=self.search_var,
            font=('Arial', 14)
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 清除搜尋按鈕
        clear_btn = ttk.Button(
            search_input_frame,
            text="✕",
            width=3,
            command=lambda: self.search_var.set('')
        )
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # 搜尋提示
        self.search_hint = ttk.Label(
            search_frame,
            text="輸入股票代碼或名稱",
            font=('Arial', 11),
            foreground='gray'
        )
        self.search_hint.pack(anchor=tk.W, pady=(5, 0))
        
        # 股票列表（使用 Treeview 替代 Listbox）
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 創建 Treeview
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 設定 Treeview 樣式
        style.configure("Stock.Treeview", font=('Arial', 13), rowheight=35)
        style.configure("Stock.Treeview.Heading", font=('Arial', 14, 'bold'))
        
        self.stock_tree = ttk.Treeview(
            list_frame,
            columns=('code', 'name'),
            show='tree headings',
            yscrollcommand=scrollbar.set,
            style="Stock.Treeview",
            selectmode='browse'
        )
        
        # 設定欄位
        self.stock_tree.heading('#0', text='')
        self.stock_tree.heading('code', text='代碼')
        self.stock_tree.heading('name', text='股票名稱')
        
        self.stock_tree.column('#0', width=30, stretch=False)
        self.stock_tree.column('code', width=80, anchor=tk.CENTER)
        self.stock_tree.column('name', width=150, anchor=tk.W)
        
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.stock_tree.yview)
        
        # 雙擊加入觀察
        self.stock_tree.bind('<Double-Button-1>', self.on_stock_double_click)
        
        # 按鈕區域
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 加入按鈕（美化版）
        add_btn = tk.Button(
            btn_frame,
            text="➕ 加入觀察清單",
            command=self.add_to_watchlist,
            font=('Arial', 15, 'bold'),
            bg='#4CAF50',
            fg='#FFFF00',  # 黃色文字
            activebackground='#45a049',
            activeforeground='#FFFF00',
            relief=tk.FLAT,
            cursor='hand2',
            padx=25,
            pady=12
        )
        add_btn.pack(fill=tk.X)
        
        # 滑鼠懸停效果
        def on_enter(e):
            add_btn.config(bg='#45a049')
        
        def on_leave(e):
            add_btn.config(bg='#4CAF50')
        
        add_btn.bind("<Enter>", on_enter)
        add_btn.bind("<Leave>", on_leave)
        
        # 統計資訊
        self.stock_count_label = ttk.Label(
            left_frame,
            text="",
            font=('Arial', 12),
            foreground='gray'
        )
        self.stock_count_label.pack(pady=(5, 10))
    
    def setup_right_panel(self, parent):
        """建立右側資料顯示面板"""
        # TODO: Phase 5 - 實作右側面板
        right_frame = ttk.Frame(parent)
        parent.add(right_frame, weight=4)
        
        # 標題
        ttk.Label(
            right_frame,
            text="觀察中的股票",
            font=('Arial', 12, 'bold')
        ).pack(pady=5)
        
        # 滾動區域
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.stocks_container = ttk.Frame(canvas)
        
        self.stocks_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.stocks_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # 空狀態提示
        self.empty_label = ttk.Label(
            self.stocks_container,
            text="📊 尚未加入任何股票\n\n請從左側清單選擇股票加入觀察",
            font=('Arial', 12),
            foreground='gray'
        )
        self.empty_label.pack(pady=50)
    
    def load_tw_stocks(self):
        """載入台灣股票清單"""
        # TODO: Phase 4.1 - 整合 twstock
        try:
            # 取得所有上市公司代碼
            self.all_stocks = []
            
            # twstock.codes 包含所有股票代碼資訊
            for code, info in twstock.codes.items():
                if info.type == '股票':  # 只顯示股票類型
                    self.all_stocks.append((code, info.name))
            
            # 依代碼排序
            self.all_stocks.sort(key=lambda x: x[0])
            
            # 顯示在 Treeview 中
            for code, name in self.all_stocks:
                self.stock_tree.insert('', tk.END, values=(code, name))
            
            # 更新統計資訊
            self.update_stock_count(len(self.all_stocks))
            
            print(f"✓ 載入 {len(self.all_stocks)} 支台灣股票")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入股票清單失敗: {e}")
    
    def update_stock_count(self, count: int, total: int = None):
        """更新股票數量統計"""
        if total is not None:
            text = f"顯示 {count} / {total} 支股票"
        else:
            text = f"共 {count} 支股票"
        self.stock_count_label.config(text=text)
    
    def on_search(self, *args):
        """搜尋框文字變更時觸發"""
        # TODO: Phase 4.3 - 實作搜尋功能
        search_text = self.search_var.get().lower()
        
        # 清空 Treeview
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 過濾並顯示符合的股票
        matched_count = 0
        for code, name in self.all_stocks:
            if search_text in code.lower() or search_text in name.lower():
                self.stock_tree.insert('', tk.END, values=(code, name))
                matched_count += 1
        
        # 更新統計資訊
        if search_text:
            self.update_stock_count(matched_count, total=len(self.all_stocks))
        else:
            self.update_stock_count(len(self.all_stocks))
    
    def on_stock_double_click(self, event):
        """雙擊股票項目時加入觀察清單"""
        self.add_to_watchlist()
    
    def add_to_watchlist(self):
        """加入股票到觀察清單"""
        # TODO: Phase 4.4 - 實作加入功能
        selection = self.stock_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "請先選擇一支股票")
            return
        
        # 取得選中的股票代碼
        item = selection[0]
        values = self.stock_tree.item(item, 'values')
        stock_code = values[0]
        
        if stock_code in self.watchlist:
            messagebox.showinfo("提示", f"股票 {stock_code} 已在觀察清單中")
            return
        
        self.watchlist.add(stock_code)
        messagebox.showinfo("成功", f"已加入股票 {stock_code} 到觀察清單")
        
        # 更新顯示
        self.update_watchlist_display()
    
    def remove_from_watchlist(self, stock_code: str):
        """從觀察清單移除股票"""
        if stock_code in self.watchlist:
            self.watchlist.remove(stock_code)
            if stock_code in self.stock_data_cache:
                del self.stock_data_cache[stock_code]
            self.update_watchlist_display()
    
    def update_watchlist_display(self):
        """更新右側觀察清單顯示"""
        # TODO: Phase 5 - 實作資料顯示
        # 清空現有顯示
        for widget in self.stocks_container.winfo_children():
            widget.destroy()
        
        if not self.watchlist:
            # 顯示空狀態
            self.empty_label = ttk.Label(
                self.stocks_container,
                text="📊 尚未加入任何股票\n\n請從左側清單選擇股票加入觀察",
                font=('Arial', 14),
                foreground='gray'
            )
            self.empty_label.pack(pady=50)
        else:
            # 使用三欄布局顯示股票卡片
            sorted_stocks = sorted(self.watchlist)
            current_row_frame = None
            
            for idx, stock_code in enumerate(sorted_stocks):
                col = idx % 3  # 0, 1, 或 2（左、中、右欄）
                
                # 為每一列創建 Frame
                if col == 0:
                    current_row_frame = ttk.Frame(self.stocks_container)
                    current_row_frame.pack(fill=tk.X, padx=5, pady=5)
                
                self.create_stock_card(stock_code, current_row_frame, col)
    
    def create_stock_card(self, stock_code: str, parent_frame: ttk.Frame, column: int):
        """
        建立股票資訊卡片
        
        Args:
            stock_code: 股票代碼
            parent_frame: 父容器
            column: 欄位編號（0 或 1）
        """
        # 主卡片容器
        card_frame = ttk.LabelFrame(
            parent_frame,
            text=f"  股票 {stock_code}  ",
            padding=15
        )
        card_frame.grid(row=0, column=column, sticky="nsew", padx=5, pady=5)
        parent_frame.columnconfigure(column, weight=1)
        
        # 取得快取資料
        stock_data = self.stock_data_cache.get(stock_code)
        
        if stock_data:
            # 內容容器
            content_frame = ttk.Frame(card_frame)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # === 標題區（股票代碼與名稱） ===
            header_frame = ttk.Frame(content_frame)
            header_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(
                header_frame,
                text=f"{stock_data.get('股票號碼', 'N/A')}",
                font=('Arial', 20, 'bold')
            ).pack(side=tk.LEFT)
            
            ttk.Label(
                header_frame,
                text=f"{stock_data.get('股票名稱', 'N/A')}",
                font=('Arial', 18)
            ).pack(side=tk.LEFT, padx=(10, 0))
            
            # === 即時價格區（大字體顯示） ===
            price_frame = ttk.Frame(content_frame)
            price_frame.pack(fill=tk.X, pady=(0, 10))
            
            price_text = stock_data.get('即時價格', 'N/A')
            price_label = tk.Label(
                price_frame,
                text=price_text,
                font=('Arial', 36, 'bold'),
                fg='black'
            )
            price_label.pack(side=tk.LEFT)
            
            # 漲跌顯示（帶顏色）
            change = stock_data.get('漲跌', 'N/A')
            change_rate = stock_data.get('漲跌百分比', 'N/A')
            
            # 判斷漲跌顏色
            color = 'black'
            if change != 'N/A' and change:
                try:
                    change_value = float(change.replace(',', ''))
                    if change_value > 0:
                        color = '#d32f2f'  # 紅色（漲）
                        change = f"▲ {change}"
                    elif change_value < 0:
                        color = '#388e3c'  # 綠色（跌）
                        change = f"▼ {change}"
                except:
                    pass
            
            change_frame = ttk.Frame(price_frame)
            change_frame.pack(side=tk.LEFT, padx=(15, 0))
            
            tk.Label(
                change_frame,
                text=change,
                font=('Arial', 20, 'bold'),
                fg=color
            ).pack()
            
            tk.Label(
                change_frame,
                text=change_rate,
                font=('Arial', 17),
                fg=color
            ).pack()
            
            # === 詳細資訊區（兩欄佈局） ===
            info_frame = ttk.Frame(content_frame)
            info_frame.pack(fill=tk.X, pady=(5, 10))
            
            # 左欄
            left_col = ttk.Frame(info_frame)
            left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            self._add_info_row(left_col, "開盤", stock_data.get('開盤價', 'N/A'))
            self._add_info_row(left_col, "最高", stock_data.get('最高價', 'N/A'))
            self._add_info_row(left_col, "最低", stock_data.get('最低價', 'N/A'))
            
            # 右欄
            right_col = ttk.Frame(info_frame)
            right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
            
            self._add_info_row(right_col, "成交量", stock_data.get('成交量(張)', 'N/A'))
            self._add_info_row(right_col, "昨收", stock_data.get('前一日收盤價', 'N/A'))
            self._add_info_row(right_col, "更新", stock_data.get('update_time', 'N/A'), size=11)
            
        else:
            # 等待資料
            ttk.Label(
                card_frame,
                text="⏳ 等待更新資料...",
                font=('Arial', 16),
                foreground='gray'
            ).pack(pady=20)
        
        # === 移除按鈕區 ===
        btn_frame = ttk.Frame(card_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 使用 tk.Button 以便自訂顏色
        remove_btn = tk.Button(
            btn_frame,
            text="✕ 移除",
            command=lambda: self.remove_from_watchlist(stock_code),
            font=('Arial', 13, 'bold'),
            bg='#f44336',
            fg='#FFFF00',  # 黃色文字
            activebackground='#d32f2f',
            activeforeground='#FFFF00',
            relief=tk.FLAT,
            cursor='hand2',
            padx=20,
            pady=8
        )
        remove_btn.pack(side=tk.RIGHT)
        
        # 滑鼠懸停效果
        def on_enter(e):
            remove_btn.config(bg='#d32f2f')
        
        def on_leave(e):
            remove_btn.config(bg='#f44336')
        
        remove_btn.bind("<Enter>", on_enter)
        remove_btn.bind("<Leave>", on_leave)
    
    def _add_info_row(self, parent, label: str, value: str, size: int = 14):
        """
        添加資訊列
        
        Args:
            parent: 父容器
            label: 標籤文字
            value: 數值
            size: 字體大小
        """
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        
        ttk.Label(
            row,
            text=f"{label}:",
            font=('Arial', size),
            foreground='#666'
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            row,
            text=value,
            font=('Arial', size, 'bold')
        ).pack(side=tk.LEFT, padx=(5, 0))
    
    def manual_update(self):
        """手動更新股票資料"""
        # TODO: Phase 6.1 - 實作手動更新
        if not self.watchlist:
            messagebox.showinfo("提示", "觀察清單為空，請先加入股票")
            return
        
        if self.is_updating:
            messagebox.showinfo("提示", "正在更新中，請稍候...")
            return
        
        self.start_update()
    
    def start_update(self):
        """開始更新股票資料"""
        self.is_updating = True
        self.update_btn.config(state=tk.DISABLED)
        self.status_label.config(text=f"🔄 更新中... (0/{len(self.watchlist)})")
        
        # 在背景執行緒中執行爬蟲
        stock_codes = list(self.watchlist)
        thread = threading.Thread(
            target=run_crawler_in_thread,
            args=(stock_codes, self.result_queue),
            daemon=True
        )
        thread.start()
    
    def check_queue(self):
        """檢查爬蟲結果佇列"""
        try:
            while True:
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == 'success':
                    self.on_update_complete(data)
                elif msg_type == 'error':
                    self.on_update_error(data)
                    
        except queue.Empty:
            pass
        
        # 每 100ms 檢查一次
        self.root.after(100, self.check_queue)
    
    def on_update_complete(self, results: List[Dict]):
        """更新完成回調"""
        # 更新快取
        for stock_data in results:
            stock_code = stock_data.get('stock_code')
            if stock_code:
                self.stock_data_cache[stock_code] = stock_data
        
        # 更新顯示
        self.update_watchlist_display()
        
        # 更新狀態
        self.is_updating = False
        self.update_btn.config(state=tk.NORMAL)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.status_label.config(text=f"✓ 更新完成")
        self.last_update_label.config(text=f"最後更新: {current_time}")
        
        print(f"✓ 成功更新 {len(results)}/{len(self.watchlist)} 支股票")
    
    def on_update_error(self, error_msg: str):
        """更新錯誤回調"""
        self.is_updating = False
        self.update_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"✗ 更新失敗")
        messagebox.showerror("錯誤", f"更新股票資料時發生錯誤:\n{error_msg}")
    
    def toggle_auto_update(self):
        """切換自動更新狀態"""
        # TODO: Phase 6.2 - 實作自動更新
        self.auto_update_enabled = self.auto_update_var.get()
        
        if self.auto_update_enabled:
            print("✓ 啟用自動更新（每 60 秒）")
            self.schedule_auto_update()
        else:
            print("✗ 停用自動更新")
            if self.update_timer_id:
                self.root.after_cancel(self.update_timer_id)
                self.update_timer_id = None
    
    def schedule_auto_update(self):
        """排程自動更新"""
        if self.auto_update_enabled and self.watchlist and not self.is_updating:
            self.start_update()
        
        # 每 60 秒執行一次
        if self.auto_update_enabled:
            self.update_timer_id = self.root.after(60000, self.schedule_auto_update)
    
    def on_closing(self):
        """視窗關閉事件處理"""
        if self.update_timer_id:
            self.root.after_cancel(self.update_timer_id)
        
        self.root.destroy()


# ==================== 主程式入口 ====================

def main():
    """應用程式主入口"""
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
