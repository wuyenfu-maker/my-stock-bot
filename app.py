import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime

# 1. 頁面配置
st.set_page_config(page_title="AI 台股全市場監測系統", layout="wide")
st.title("🇹🇼 台股全市場 AI 監測 (含興櫃、上市、上櫃)")

# 2. 快取：抓取全市場股票代碼與中英文對照表
@st.cache_data
def get_stock_mapping():
    api = DataLoader()
    # 抓取全市場基本資訊
    df_info = api.taiwan_stock_info()
    # 這裡的 df_info 包含了上市 (Taiwan Stock Exchange)、上櫃 (OTC)、興櫃 (Emerging)
    # 我們整理出：代號, 中文名, 英文名
    return df_info

stock_map_df = get_stock_mapping()

# 3. 核心數據處理函數
def get_detailed_stock_info(sid):
    # 從 FinMind 對照表找名字
    info_row = stock_map_df[stock_map_df['stock_id'] == sid]
    if info_row.empty:
        return None
    
    ch_name = info_row['stock_name'].values[0]
    # yfinance 獲取英文名與即時價格
    # 台灣股票後綴邏輯：興櫃與上櫃通常用 .TWO，上市用 .TW
    # 我們嘗試自動判斷，先試 .TW 再試 .TWO
    ticker_str = f"{sid}.TW"
    tk = yf.Ticker(ticker_str)
    
    try:
        price = tk.fast_info.last_price
        if price == 0 or price is None: # 如果抓不到，換 .TWO 試試
            ticker_str = f"{sid}.TWO"
            tk = yf.Ticker(ticker_str)
            price = tk.fast_info.last_price
    except:
        ticker_str = f"{sid}.TWO"
        tk = yf.Ticker(ticker_str)
        price = tk.fast_info.last_price

    en_name = tk.info.get('shortName', 'N/A')
    
    # 建議購買價計算 (5日/10日均線)
    hist = tk.history(period="1mo")
    suggest_price = 0
    if not hist.empty:
        ma5 = hist['Close'].rolling(5).mean().iloc[-1]
        ma10 = hist['Close'].rolling(10).mean().iloc[-1]
        suggest_price = round((ma5 + ma10) / 2, 2)

    return {
        "Stock ID": sid,
        "中文名稱": ch_name,
        "English Name": en_name,
        "目前股價": price,
        "建議買入價": suggest_price,
        "市場類別": info_row['industry_category'].values[0]
    }

# 4. 事件選股邏輯 (加入興櫃標的)
def event_logic(keyword):
    analysis = {
        "委瑞內拉": {
            "impact": "地緣政治影響油價與航運，興櫃能源股可能受連動。",
            "stocks": ["1301", "2603", "6505", "6901"] # 6901 示例興櫃/上櫃能源相關
        },
        "AI": {
            "impact": "CES 2026 引發算力需求，除權值股外，可關注興櫃之微散熱或IC設計。",
            "stocks": ["2330", "2382", "6695", "6719"] # 6719 力智等
        }
    }
    for key in analysis:
        if key in keyword:
            return analysis[key]
    return None

# --- 主介面 ---
st.sidebar.header("🔍 全市場搜尋")
keyword = st.sidebar.text_input("輸入事件關鍵字 (如: 委瑞內拉、AI)", "")

if keyword:
    res = event_logic(keyword)
    if res:
        st.success(f"💡 AI 深度分析：{res['impact']}")
        
        table_data = []
        for sid in res['stocks']:
            with st.spinner(f"正在抓取數據: {sid}..."):
                info = get_detailed_stock_info(sid)
                if info:
                    table_data.append(info)
        
        if table_data:
            df_result = pd.DataFrame(table_data)
            st.markdown("### 📊 推薦關注清單 (含中英文資訊)")
            st.dataframe(df_result, use_container_width=True)
            
            # 選購建議
            for item in table_data:
                st.write(f"👉 **{item['中文名稱']} ({item['English Name']})**: "
                         f"現價 {item['目前股價']}，建議關注價 **{item['建議買入價']}**")
    else:
        st.warning("查無此事件，請輸入精確關鍵字或嘗試手動搜尋個股。")

st.markdown("---")
# 手動查詢區
st.subheader("🔎 個股快速診斷")
manual_sid = st.text_input("輸入任何股票代號 (如 2330 或 興櫃代號)", "")
if manual_sid:
    m_info = get_detailed_stock_info(manual_sid)
    if m_info:
        col1, col2 = st.columns(2)
        col1.metric("中文名稱", m_info['中文名稱'])
        col2.metric("English Name", m_info['English Name'])
        st.json(m_info)
    else:
        st.error("找不到該股票代號，請確認輸入是否正確。")
