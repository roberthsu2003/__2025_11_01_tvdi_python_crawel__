"""
台灣銀行匯率查詢系統 - tkinter 桌面應用程式

整合 crawl4ai 爬蟲與 tkinter GUI，提供即時匯率查詢與台幣轉換功能。
"""

import asyncio
import json
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from datetime import datetime
from typing import Optional, List, Dict

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


# ============= 爬蟲模組 =============

async def fetch_exchange_rates() -> Optional[List[Dict[str, str]]]:
    """
    爬取台灣銀行匯率資訊
    
    Returns:
        匯率資料列表，格式:
        [
            {
                "幣別": "美金 (USD)",
                "本行即期買入": "31.50",
                "本行即期賣出": "32.50"
            },
            ...
        ]
        失敗時返回 None
    """
    try:
        # 定義資料提取 schema
        schema = {
            "name": "匯率資訊",
            "baseSelector": "table[title='牌告匯率'] tr",
            "fields": [
                {
                    "name": "幣別",
                    "selector": "td[data-table='幣別'] div.print_show",
                    "type": "text"
                },
                {
                    "name": "本行即期買入",
                    "selector": "td[data-table='本行即期買入']",
                    "type": "text"
                },
                {
                    "name": "本行即期賣出",
                    "selector": "td[data-table='本行即期賣出']",
                    "type": "text"
                }
            ]
        }

        # 建立提取策略
        extraction_strategy = JsonCssExtractionStrategy(schema)

        # 配置爬蟲
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy
        )

        # 執行爬蟲
        async with AsyncWebCrawler() as crawler:
            url = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
            result = await crawler.arun(url=url, config=run_config)
            data = json.loads(result.extracted_content)
            
            # 清理資料
            cleaned_data = []
            for item in data:
                currency = item.get("幣別", "").strip()
                buy_rate = item.get("本行即期買入", "").strip()
                sell_rate = item.get("本行即期賣出", "").strip()
                
                # 只加入有幣別資料的項目
                if currency:
                    cleaned_data.append({
                        "幣別": currency,
                        "本行即期買入": buy_rate,
                        "本行即期賣出": sell_rate
                    })
            
            return cleaned_data if cleaned_data else None
            
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
        return None


# ============= GUI 應用程式 =============

class ExchangeRateApp(tk.Tk):
    """匯率查詢應用程式主視窗"""
    
    def __init__(self):
        """初始化應用程式"""
        super().__init__()
        
        # 視窗基本設定
        self.title("台灣銀行匯率查詢系統")
        self.geometry("1200x750")
        self.resizable(True, True)
        self.configure(bg="#f0f0f0")
        
        # 資料儲存
        self.exchange_data: List[Dict[str, str]] = []
        self.last_update: Optional[datetime] = None
        self.is_loading: bool = False
        
        # 建立 UI
        self._setup_ui()
        
        # 載入初始資料
        self._load_initial_data()
    
    def _setup_ui(self):
        """建立 UI 元件"""
        # 建立主容器
        main_container = ttk.Frame(self, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置主視窗權重
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # ===== 標題欄 =====
        header_frame = ttk.Frame(main_container, relief="raised", borderwidth=2)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15), ipady=10)
        
        # 標題
        title_label = ttk.Label(
            header_frame, 
            text="🏦 台灣銀行匯率查詢系統",
            font=("Arial", 24, "bold"),
            foreground="#2c3e50"
        )
        title_label.grid(row=0, column=0, sticky=tk.W, padx=15)
        
        # 更新按鈕
        self.update_btn = ttk.Button(
            header_frame,
            text="🔄 更新匯率",
            command=self._manual_update,
            style="Large.TButton"
        )
        self.update_btn.grid(row=0, column=1, padx=20, pady=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(header_frame, text="", foreground="#27ae60", font=("Arial", 14, "bold"))
        self.status_label.grid(row=0, column=2, padx=15)
        
        # 最後更新時間
        self.time_label = ttk.Label(header_frame, text="", foreground="#7f8c8d", font=("Arial", 14))
        self.time_label.grid(row=0, column=3, padx=15)
        
        # ===== 左側 - 匯率表格 =====
        left_frame = ttk.LabelFrame(main_container, text="  📊 匯率資訊  ", padding="15")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 8))
        
        # 設定 Treeview 樣式
        style = ttk.Style()
        style.configure("Large.Treeview", font=("Arial", 14), rowheight=35)
        style.configure("Large.Treeview.Heading", font=("Arial", 16, "bold"), background="#3498db", foreground="white")
        
        # 建立 Treeview
        columns = ("幣別", "本行即期買入", "本行即期賣出")
        self.tree = ttk.Treeview(
            left_frame,
            columns=columns,
            show="headings",
            height=15,
            style="Large.Treeview"
        )
        
        # 設定欄位
        self.tree.heading("幣別", text="幣別")
        self.tree.heading("本行即期買入", text="本行即期買入")
        self.tree.heading("本行即期賣出", text="本行即期賣出")
        
        # 設定欄寬
        self.tree.column("幣別", width=200, anchor=tk.W)
        self.tree.column("本行即期買入", width=160, anchor=tk.CENTER)
        self.tree.column("本行即期賣出", width=160, anchor=tk.CENTER)
        
        # 捲軸
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 佈局
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置左側框架權重
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        # ===== 右側 - 台幣轉換計算器 =====
        right_frame = ttk.LabelFrame(main_container, text="  💱 台幣轉換計算器  ", padding="20")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(8, 0))
        
        # 說明文字
        instruction = ttk.Label(
            right_frame,
            text="✨ 輸入台幣金額，選擇目標貨幣進行轉換",
            font=("Arial", 14),
            foreground="#34495e"
        )
        instruction.grid(row=0, column=0, columnspan=2, pady=(0, 25))
        
        # 台幣輸入
        ttk.Label(right_frame, text="💵 台幣金額 (TWD):", font=("Arial", 16)).grid(row=1, column=0, sticky=tk.W, pady=10)
        self.twd_entry = ttk.Entry(right_frame, width=18, font=("Arial", 16))
        self.twd_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))
        
        # 目標貨幣選擇
        ttk.Label(right_frame, text="🌍 目標貨幣:", font=("Arial", 16)).grid(row=2, column=0, sticky=tk.W, pady=10)
        self.currency_combo = ttk.Combobox(right_frame, width=16, state="readonly", font=("Arial", 16))
        self.currency_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))
        
        # 設定按鈕樣式
        style.configure("Large.TButton", font=("Arial", 16, "bold"), padding=15)
        
        # 計算按鈕
        calc_btn = ttk.Button(
            right_frame,
            text="💱 計算轉換",
            command=self._calculate_conversion,
            style="Large.TButton"
        )
        calc_btn.grid(row=3, column=0, columnspan=2, pady=25, ipadx=20, ipady=5)
        
        # 結果顯示區
        result_frame = ttk.LabelFrame(right_frame, text="  📊 轉換結果  ", padding="15")
        result_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=15)
        
        self.result_text = tk.Text(
            result_frame,
            font=("Arial", 14),
            state="disabled",
            wrap=tk.WORD
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置結果框架權重，讓文字框能夠擴展
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 說明文字
        help_text = ttk.Label(
            right_frame,
            text="💡 買入：您賣台幣給銀行\n💡 賣出：您向銀行買外幣",
            font=("Arial", 13),
            foreground="#7f8c8d",
            justify=tk.LEFT
        )
        help_text.grid(row=5, column=0, columnspan=2, pady=(15, 0))
        
        # 配置右側框架權重
        right_frame.columnconfigure(1, weight=1)
        right_frame.rowconfigure(4, weight=1)  # 讓結果顯示區能夠擴展
        
        # ===== 配置主容器權重 =====
        main_container.columnconfigure(0, weight=2)  # 左側較寬
        main_container.columnconfigure(1, weight=1)  # 右側較窄
        main_container.rowconfigure(1, weight=1)
    
    def _load_initial_data(self):
        """載入初始資料"""
        self._fetch_data_thread()
    
    def _manual_update(self):
        """手動更新匯率"""
        if not self.is_loading:
            self._fetch_data_thread()
    
    def _fetch_data_thread(self):
        """在背景執行緒中爬取資料"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self._show_loading()
        
        def run_async():
            """在新的事件迴圈中執行非同步函數"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(fetch_exchange_rates())
                # 使用 after 確保在主執行緒中更新 UI
                self.after(0, lambda: self._update_ui_with_data(data))
            except Exception as e:
                self.after(0, lambda: self._show_error(f"爬蟲失敗: {str(e)}"))
            finally:
                loop.close()
                self.is_loading = False
        
        # 啟動背景執行緒
        thread = Thread(target=run_async, daemon=True)
        thread.start()
    
    def _show_loading(self):
        """顯示載入狀態"""
        self.status_label.config(text="⏳ 載入中...", foreground="#3498db")
        self.update_btn.config(state="disabled")
        self.config(cursor="watch")
    
    def _hide_loading(self):
        """隱藏載入狀態"""
        self.status_label.config(text="")
        self.update_btn.config(state="normal")
        self.config(cursor="")
    
    def _update_ui_with_data(self, data: Optional[List[Dict[str, str]]]):
        """更新 UI 資料"""
        self._hide_loading()
        
        if data is None or len(data) == 0:
            messagebox.showerror("錯誤", "無法取得匯率資料，請檢查網路連線或稍後再試")
            return
        
        # 儲存資料
        self.exchange_data = data
        self.last_update = datetime.now()
        
        # 更新表格
        self._update_treeview()
        
        # 更新下拉選單
        self._update_currency_combo()
        
        # 更新時間標籤
        self.time_label.config(
            text=f"最後更新: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # 顯示成功訊息
        self.status_label.config(text="✅ 更新成功", foreground="#27ae60")
        self.after(3000, lambda: self.status_label.config(text=""))
    
    def _update_treeview(self):
        """更新 Treeview 資料"""
        # 清空舊資料
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 插入新資料
        for item in self.exchange_data:
            currency = item.get("幣別", "N/A")
            buy = item.get("本行即期買入", "").strip()
            sell = item.get("本行即期賣出", "").strip()
            
            # 空值處理
            buy_display = buy if buy else "暫停交易"
            sell_display = sell if sell else "暫停交易"
            
            self.tree.insert("", "end", values=(currency, buy_display, sell_display))
    
    def _update_currency_combo(self):
        """更新貨幣下拉選單（過濾無法交易的貨幣）"""
        available_currencies = []
        
        for item in self.exchange_data:
            currency = item.get("幣別", "")
            buy = item.get("本行即期買入", "").strip()
            sell = item.get("本行即期賣出", "").strip()
            
            # 只加入可交易的貨幣（買入和賣出都有值）
            if currency and buy and sell:
                available_currencies.append(currency)
        
        self.currency_combo['values'] = available_currencies
        
        # 如果有可用貨幣，設定預設選擇
        if available_currencies:
            self.currency_combo.current(0)
    
    def _calculate_conversion(self):
        """計算台幣轉換"""
        try:
            # 取得輸入
            twd_text = self.twd_entry.get().strip()
            if not twd_text:
                messagebox.showwarning("警告", "請輸入台幣金額")
                return
            
            twd_amount = float(twd_text)
            if twd_amount <= 0:
                messagebox.showwarning("警告", "金額必須大於 0")
                return
            
            selected_currency = self.currency_combo.get()
            if not selected_currency:
                messagebox.showwarning("警告", "請選擇目標貨幣")
                return
            
            # 查找匯率
            rate_data = self._find_rate_by_currency(selected_currency)
            if not rate_data:
                messagebox.showerror("錯誤", "找不到該貨幣的匯率")
                return
            
            buy_rate_str = rate_data["本行即期買入"]
            sell_rate_str = rate_data["本行即期賣出"]
            
            if not buy_rate_str or not sell_rate_str:
                messagebox.showerror("錯誤", "該貨幣暫停交易")
                return
            
            buy_rate = float(buy_rate_str)
            sell_rate = float(sell_rate_str)
            
            # 計算轉換
            # 買入：使用者賣台幣給銀行，用買入匯率
            buy_result = twd_amount / buy_rate
            # 賣出：使用者向銀行買外幣，用賣出匯率
            sell_result = twd_amount / sell_rate
            
            # 顯示結果
            result_text = f"""
═══════════════════════════
💰 轉換金額: {twd_amount:,.2f} 台幣
🌍 目標貨幣: {selected_currency}
═══════════════════════════

📤 您賣台幣給銀行 (買入匯率)
   匯率: {buy_rate}
   可得: {buy_result:.2f} 外幣

📥 您向銀行買外幣 (賣出匯率)
   匯率: {sell_rate}
   需付: {sell_result:.2f} 外幣

═══════════════════════════
計算時間: {datetime.now().strftime('%H:%M:%S')}
"""
            
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result_text)
            self.result_text.config(state="disabled")
            
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的數字金額")
        except Exception as e:
            messagebox.showerror("錯誤", f"計算失敗: {str(e)}")
    
    def _find_rate_by_currency(self, currency: str) -> Optional[Dict[str, str]]:
        """根據幣別查找匯率資料"""
        for item in self.exchange_data:
            if item.get("幣別") == currency:
                return item
        return None
    
    def _show_error(self, message: str):
        """顯示錯誤訊息"""
        self._hide_loading()
        messagebox.showerror("錯誤", message)


# ============= 主程式入口 =============

def main():
    """應用程式入口"""
    app = ExchangeRateApp()
    app.mainloop()


if __name__ == "__main__":
    main()
