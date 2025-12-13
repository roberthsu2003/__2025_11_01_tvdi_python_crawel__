import asyncio
import json
from datetime import datetime
import streamlit as st
import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


@st.cache_data(ttl=600)  # 10分鐘快取
def fetch_exchange_rates():
    """爬取台灣銀行匯率資料"""
    
    async def _fetch():
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

        strategy = JsonCssExtractionStrategy(schema)
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=strategy
        )
        
        async with AsyncWebCrawler() as crawler:
            url = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
            result = await crawler.arun(url=url, config=run_config)
            data = json.loads(result.extracted_content)
            return data
    
    # 執行非同步函數
    data = asyncio.run(_fetch())
    
    # 轉換為 DataFrame
    df = pd.DataFrame(data)
    
    # 處理資料
    if not df.empty:
        # 處理空值顯示為「暫停交易」
        df['本行即期買入'] = df['本行即期買入'].replace('', '暫停交易').fillna('暫停交易')
        df['本行即期賣出'] = df['本行即期賣出'].replace('', '暫停交易').fillna('暫停交易')
        
        # 過濾掉無法交易的貨幣（買入和賣出都是暫停交易的）
        df = df[~((df['本行即期買入'] == '暫停交易') & (df['本行即期賣出'] == '暫停交易'))]
    
    return df


def main():
    st.set_page_config(
        page_title="台幣匯率轉換",
        page_icon="💱",
        layout="wide"
    )
    
    st.title("💱 台幣匯率轉換系統")
    st.markdown("---")
    
    # 手動更新按鈕
    col_update = st.columns([6, 1])[1]
    with col_update:
        if st.button("🔄 手動更新", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # 顯示更新時間
    st.info(f"📅 最後更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 獲取匯率資料
    try:
        df = fetch_exchange_rates()
        
        if df.empty:
            st.error("❌ 無法取得匯率資料")
            return
        
        # 建立兩欄布局
        col1, col2 = st.columns([1, 1])
        
        # 左欄：顯示匯率表格
        with col1:
            st.subheader("📊 台灣銀行牌告匯率")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=600
            )
        
        # 右欄：台幣轉換計算器
        with col2:
            st.subheader("💰 台幣轉換計算器")
            
            # 過濾可交易的貨幣（至少有一個欄位不是暫停交易）
            tradable_df = df[
                (df['本行即期買入'] != '暫停交易') | 
                (df['本行即期賣出'] != '暫停交易')
            ].copy()
            
            if tradable_df.empty:
                st.warning("⚠️ 目前沒有可交易的貨幣")
                return
            
            # 輸入台幣金額
            twd_amount = st.number_input(
                "輸入台幣金額 (TWD)",
                min_value=0.0,
                value=10000.0,
                step=100.0,
                format="%.2f"
            )
            
            # 選擇目標貨幣
            currency_list = tradable_df['幣別'].tolist()
            selected_currency = st.selectbox(
                "選擇目標貨幣",
                currency_list
            )
            
            # 計算轉換
            if selected_currency:
                selected_row = tradable_df[tradable_df['幣別'] == selected_currency].iloc[0]
                
                st.markdown("---")
                st.markdown(f"### 📈 {selected_currency} 匯率資訊")
                
                # 顯示匯率資訊
                col_buy, col_sell = st.columns(2)
                
                with col_buy:
                    buy_rate = selected_row['本行即期買入']
                    st.metric(
                        "本行買入",
                        buy_rate if buy_rate != '暫停交易' else '暫停交易'
                    )
                    
                with col_sell:
                    sell_rate = selected_row['本行即期賣出']
                    st.metric(
                        "本行賣出",
                        sell_rate if sell_rate != '暫停交易' else '暫停交易'
                    )
                
                st.markdown("---")
                st.markdown("### 💵 轉換結果")
                
                # 計算轉換金額（使用銀行賣出匯率，因為客戶是買外幣）
                if sell_rate != '暫停交易':
                    try:
                        sell_rate_float = float(sell_rate)
                        foreign_amount = twd_amount / sell_rate_float
                        
                        st.success(
                            f"**{twd_amount:,.2f} TWD** = "
                            f"**{foreign_amount:,.4f} {selected_currency}**"
                        )
                        
                        st.caption(f"使用匯率：{sell_rate_float:.4f} (本行賣出)")
                    except ValueError:
                        st.error("❌ 匯率資料格式錯誤")
                else:
                    st.warning("⚠️ 此貨幣暫停交易")
    
    except Exception as e:
        st.error(f"❌ 發生錯誤：{str(e)}")


if __name__ == "__main__":
    main()