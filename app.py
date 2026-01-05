import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from FinMind.data import DataLoader
import datetime
import time

# 1. 頁面配置 (必須放在最上方)
st.set_page_config(page_title="AI 台股全能監測站", layout="wide")

# 2. 資料快取與載入
api = DataLoader()

@st.cache_data(ttl=3600)
def get_stock_list():
    # 抓取全市場清單 (含中英文、行業)
    return api.taiwan_stock_info()

stock_df = get_stock_list()

# 3. 側邊欄佈局 (確保先顯示 UI，不被報錯卡住)
st.sidebar.title("🎯 智慧投資選股")

# A. 新聞搜尋
st.sidebar.subheader("📰 事件驅動搜尋")
news_q = st.sidebar.text_input("搜尋關鍵字 (如: 委內瑞拉, AI)", "")

# B. 行業分類
st.sidebar.subheader("🏭 行業快速掃描")
ind_list = ["請選擇"] + sorted(stock_df['industry_category'].unique().tolist())
selected_ind = st.sidebar.selectbox("選取行業標的", ind_list)

# C. 手動輸入
st.sidebar.subheader("🔢 自選股追蹤")
manual_ids = st.sidebar.text_input("輸入代碼 (用逗號隔開)", "2330, 2454")

# --- 4. 智慧分析邏輯 ---
EVENT_DB = {
    "委內瑞拉": {"desc": "地緣局勢推升原油與航運報價", "stocks": ["1301", "2603", "6505"]},
    "AI": {"desc": "CES 2026 引領算力需求與硬體升級", "stocks": ["2330", "2454", "2382"]}
}

def analyze_stock_safe(sid):
    """防禦性數據抓取，移除所有 tk.info 以防封鎖"""
    suffix = ".TW"
    tk = yf.Ticker(f"{sid}{suffix}")
    hist = tk.history(period="3mo")
    
    if hist.empty: # 嘗試二進制
        suffix = ".TWO"
        tk = yf.Ticker(f"{sid}{suffix}")
        hist = tk.history(period="3mo")
    
    if hist.empty: return None

    # 獲取名稱 (從 FinMind 獲取，不使用 yfinance 以節省流量)
    name_info = stock_df[stock_df['stock_id'] == sid]
    cn_name = name_info['stock_name'].values[0] if not name_info.empty else sid
    
    price = tk.fast_info.last_price
    v5 = int(hist['Volume'].tail(5).mean() / 1000)
    v20 = int(hist['Volume'].tail(20).mean() / 1000)
    # 建議價: 月線支撐
    ma20 = hist['Close'].rolling(20).mean().iloc[-1]

    return {
        "sid": sid, "cn": cn_name, "price": price, 
        "v5": v5, "v20": v20, "ma20": round(ma20, 2), "hist": hist
    }

# --- 5. 主畫面執行 ---
st.title("🚀 2026 台股 AI 決策系統")

# 決定要跑哪些股票
stocks_to_run = []
if news_q:
    match = next((v for k, v in EVENT_DB.items() if k in news_q), None)
    if match:
        st.success(f"💡 AI 觀點：{match['desc']}")
        stocks_to_run = match['stocks']
    else:
        st.warning("目前暫無此關鍵字數據，試試『委內瑞拉』")
elif selected_ind != "請選擇":
    # 為了防止封鎖，行業掃描嚴格限制只顯示前 3 支
    stocks_to_run = stock_df[stock_df['industry_category'] == selected_ind]['stock_id'].head(3).tolist()
    st.info(f"📍 掃描 {selected_ind} 前 3 名個股 (防止 API 流量過載)")
elif manual_ids:
    stocks_to_run = [s.strip() for s in manual_ids.split(",") if s.strip()]

# 執行與呈現
if stocks_to_run:
    for sid in stocks_to_run:
        with st.spinner(f"正在安全讀取 {sid}..."):
            data = analyze_stock_safe(sid)
            time.sleep(1.2) # 重要：強制休眠 1.2 秒防止被 Yahoo 封鎖
            
            if data:
                st.subheader(f"📈 {data['sid']} {data['cn']}")
                col1, col2 = st.columns([3, 1])
                with col1:
                    fig = go.Figure(data=[go.Candlestick(x=data['hist'].index, open=data['hist']['Open'], high=data['hist']['High'], low=data['hist']['Low'], close=data['hist']['Close'])])
                    fig.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.metric("即時股價", f"{data['price']:.2f}")
                    st.metric("建議買入價 (支撐)", f"{data['ma20']}")
                    st.write(f"5日均量: {data['v5']} 張")
                    st.write(f"月均量: {data['v20']} 張")
                st.divider()
else:
    st.info("👈 請由左側側邊欄輸入搜尋條件。")

st.markdown("---")
st.caption("🚨 注意：本系統已啟動流量保護模式，行業掃描僅限前 3 支標的。")
