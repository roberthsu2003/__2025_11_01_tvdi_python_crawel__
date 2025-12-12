"""
台灣銀行匯率即時查詢系統 - GUI 應用程式

這是一個美觀的桌面應用程式，用於即時顯示台灣銀行的牌告匯率。
支援自動更新和手動更新功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
from datetime import datetime
from typing import Optional, List, Dict
from crawler_module import ExchangeRateCrawler


class ExchangeRateApp:
    """台灣銀行匯率查詢 GUI 應用程式"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("台灣銀行匯率即時查詢系統")
        self.root.geometry("1000x650")
        self.root.resizable(True, True)
        
        # 爬蟲實例
        self.crawler = ExchangeRateCrawler(verbose=False)
        
        # 狀態變數
        self.last_update_time = None
        self.auto_update_enabled = tk.BooleanVar(value=True)
        self.is_fetching = False
        self.update_thread = None
        self.stop_auto_update = threading.Event()
        
        # 設定樣式
        self._setup_styles()
        
        # 建立 UI
        self._create_widgets()
        
        # 初始載入資料
        self.refresh_data()
        
        # 啟動自動更新
        self._start_auto_update()
        
        # 設定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_styles(self):
        """設定 ttk 樣式"""
        style = ttk.Style()
        
        # 使用 clam 主題作為基礎
        style.theme_use('clam')
        
        # 配色方案
        self.colors = {
            'primary': '#2c3e50',      # 深藍灰
            'secondary': '#34495e',    # 中藍灰
            'accent': '#3498db',       # 亮藍
            'success': '#27ae60',      # 綠色
            'danger': '#e74c3c',       # 紅色
            'warning': '#f39c12',      # 橙色
            'bg': '#ecf0f1',          # 淺灰背景
            'fg': '#2c3e50',          # 深色文字
            'white': '#ffffff',        # 白色
        }
        
        # 主框架樣式
        style.configure('Main.TFrame', background=self.colors['bg'])
        
        # 標題樣式
        style.configure('Title.TLabel',
                       background=self.colors['primary'],
                       foreground=self.colors['white'],
                       font=('Arial', 16, 'bold'),
                       padding=15)
        
        # 資訊標籤樣式
        style.configure('Info.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       font=('Arial', 11))
        
        # 狀態列樣式
        style.configure('Status.TLabel',
                       background=self.colors['secondary'],
                       foreground=self.colors['white'],
                       font=('Arial', 10),
                       padding=8)
        
        # 按鈕樣式
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['white'],
                       font=('Arial', 11, 'bold'),
                       padding=10)
        
        # Treeview 樣式
        style.configure('Treeview',
                       background=self.colors['white'],
                       foreground=self.colors['fg'],
                       rowheight=30,
                       fieldbackground=self.colors['white'],
                       font=('Arial', 10))
        
        style.configure('Treeview.Heading',
                       background=self.colors['secondary'],
                       foreground=self.colors['white'],
                       font=('Arial', 11, 'bold'),
                       padding=8)
        
        style.map('Treeview',
                 background=[('selected', self.colors['accent'])])
        
        style.map('Treeview.Heading',
                 background=[('active', self.colors['primary'])])
    
    def _create_widgets(self):
        """建立所有 UI 元件"""
        # 主容器
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題區
        self._create_header(main_frame)
        
        # 資訊區
        self._create_info_section(main_frame)
        
        # 表格區
        self._create_table_section(main_frame)
        
        # 控制區
        self._create_control_section(main_frame)
        
        # 狀態列
        self._create_status_bar(main_frame)
    
    def _create_header(self, parent):
        """建立標題區"""
        header_frame = ttk.Frame(parent, style='Main.TFrame')
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # 標題標籤
        title = ttk.Label(header_frame,
                         text="🏦 台灣銀行匯率即時查詢系統",
                         style='Title.TLabel')
        title.pack(fill=tk.X)
    
    def _create_info_section(self, parent):
        """建立資訊區"""
        info_frame = ttk.Frame(parent, style='Main.TFrame')
        info_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 最後更新時間
        self.update_time_label = ttk.Label(info_frame,
                                          text="最後更新: 尚未更新",
                                          style='Info.TLabel')
        self.update_time_label.pack(side=tk.LEFT)
        
        # 更新按鈕
        refresh_btn = ttk.Button(info_frame,
                                text="🔄 手動更新",
                                command=self.refresh_data,
                                style='Accent.TButton')
        refresh_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_table_section(self, parent):
        """建立表格區"""
        table_frame = ttk.Frame(parent, style='Main.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 建立 Treeview
        columns = ('幣名', '現金買入', '現金賣出', '即期買入', '即期賣出')
        self.tree = ttk.Treeview(table_frame,
                                columns=columns,
                                show='headings',
                                selectmode='browse')
        
        # 設定欄位
        column_widths = {
            '幣名': 150,
            '現金買入': 110,
            '現金賣出': 110,
            '即期買入': 110,
            '即期賣出': 110
        }
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col,
                           width=column_widths.get(col, 100),
                           anchor=tk.CENTER)
        
        # 垂直捲軸
        vsb = ttk.Scrollbar(table_frame,
                           orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # 佈局
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 設定斑馬條紋
        self.tree.tag_configure('oddrow', background='#f8f9fa')
        self.tree.tag_configure('evenrow', background='#ffffff')
    
    def _create_control_section(self, parent):
        """建立控制區"""
        control_frame = ttk.Frame(parent, style='Main.TFrame')
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 自動更新開關
        auto_update_cb = ttk.Checkbutton(control_frame,
                                        text="⏰ 自動更新（每10分鐘）",
                                        variable=self.auto_update_enabled,
                                        command=self._toggle_auto_update)
        auto_update_cb.pack(side=tk.LEFT)
    
    def _create_status_bar(self, parent):
        """建立狀態列"""
        status_frame = ttk.Frame(parent, style='Main.TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame,
                                     text="● 就緒",
                                     style='Status.TLabel')
        self.status_label.pack(fill=tk.X)
    
    def _update_table(self, data: List[Dict]):
        """更新表格資料"""
        # 清空現有資料
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 插入新資料
        for idx, row in enumerate(data):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            values = (
                row.get('幣名', '-'),
                row.get('現金匯率_本行買入', '-'),
                row.get('現金匯率_本行賣出', '-'),
                row.get('即期匯率_本行買入', '-'),
                row.get('即期匯率_本行賣出', '-')
            )
            self.tree.insert('', tk.END, values=values, tags=(tag,))
    
    def refresh_data(self):
        """手動刷新資料"""
        if self.is_fetching:
            return
        
        # 在背景執行緒中執行
        thread = threading.Thread(target=self._fetch_data_async, daemon=True)
        thread.start()
    
    def _fetch_data_async(self):
        """在背景執行緒中異步抓取資料"""
        self.is_fetching = True
        self._update_status("● 正在更新資料...")
        
        try:
            # 建立新的 event loop 供此執行緒使用
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 執行異步抓取
            result = loop.run_until_complete(self.crawler.fetch_exchange_rates())
            
            loop.close()
            
            # 在主執行緒更新 UI
            self.root.after(0, self._handle_fetch_result, result)
            
        except Exception as e:
            error_msg = f"更新失敗: {str(e)}"
            self.root.after(0, self._show_error, error_msg)
        finally:
            self.is_fetching = False
    
    def _handle_fetch_result(self, result: Dict):
        """處理抓取結果"""
        if result['success']:
            # 更新表格
            self._update_table(result['data'])
            
            # 更新時間
            self.last_update_time = datetime.now()
            time_str = self.last_update_time.strftime("%Y-%m-%d %H:%M:%S")
            self.update_time_label.config(text=f"最後更新: {time_str}")
            
            # 更新狀態
            status_msg = f"● 已連線 | 共 {result['count']} 筆匯率資料"
            self._update_status(status_msg)
            
            # 儲存資料
            if result['data']:
                self.crawler.save_to_json(result['data'])
        else:
            self._show_error(f"抓取失敗: {result.get('error', '未知錯誤')}")
            self._update_status("● 連線失敗")
    
    def _show_error(self, message: str):
        """顯示錯誤訊息"""
        messagebox.showerror("錯誤", message)
    
    def _update_status(self, message: str):
        """更新狀態列"""
        self.status_label.config(text=message)
    
    def _toggle_auto_update(self):
        """切換自動更新狀態"""
        if self.auto_update_enabled.get():
            self._start_auto_update()
        else:
            self._stop_auto_update()
    
    def _start_auto_update(self):
        """啟動自動更新"""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.stop_auto_update.clear()
        self.update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self.update_thread.start()
    
    def _stop_auto_update(self):
        """停止自動更新"""
        self.stop_auto_update.set()
    
    def _auto_update_loop(self):
        """自動更新迴圈"""
        while not self.stop_auto_update.is_set():
            # 等待 10 分鐘 (600 秒)
            if self.stop_auto_update.wait(timeout=600):
                break
            
            # 如果自動更新仍然啟用，則刷新資料
            if self.auto_update_enabled.get():
                self.root.after(0, self.refresh_data)
    
    def _on_closing(self):
        """關閉應用程式時的清理"""
        self._stop_auto_update()
        self.root.destroy()


def main():
    """主程式入口"""
    root = tk.Tk()
    app = ExchangeRateApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
