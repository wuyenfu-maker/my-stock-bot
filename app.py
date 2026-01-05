import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from FinMind.data import DataLoader
import datetime
import time

# 1. 初始化與快取設定 (避免流量限制)
st.set_page_config(page_title="AI 智慧事件選股系統", layout="wide")

@st.cache_data(ttl=3600) # 股票清單快取 1 小時
def get_stock_list():
    api = DataLoader()
    return api.taiwan_stock_info()

@st.cache_data(ttl=600) # 個股歷史數據快取 10 分鐘
def fetch_hist(sid, suffix=".TW"):
    tk = yf.Ticker(f"{sid}{suffix}")
    h = tk.history(period="3mo")
    if h.empty and suffix == ".TW": # 嘗試二進制後綴 (上櫃/興櫃)
        tk = yf.Ticker(f"{sid}.TWO")
        h = tk.history(period="3mo")
    return h, tk.info.get('shortName', 'N/A'), tk.fast_info.last_price

# 2. 智慧映射庫 (支援委內瑞拉、AI等)
EVENT_DB = {
    "委內瑞拉": {"desc": "地緣政治動盪推升油價與航運報價", "stocks": ["1301", "2603", "6505"]},
    "AI": {"desc": "2026 CES 展引領算力需求", "stocks": ["2330", "2454", "2382", "3017"]},
    "機器人": {"desc": "人形機器人與自動化產業擴張", "stocks": ["2359", "2360", "4583"]}
}

# --- 3. 左側側邊欄配置 (修正紅圈位置) ---
st.sidebar.title("🔍 選股與分析配置")

# A. 新聞事件搜尋
st.sidebar.subheader("📰 新聞事件搜尋")
news_q = st.sidebar.text_input("輸入事件 (如: 委內瑞拉, AI)", "")

# B. 行業分類
st.sidebar.subheader("🏭 行業分類選擇")
df_all = get_stock_list()
industries = ["請選擇"] + sorted(df_all['industry_category'].unique().tolist())
selected_ind = st.sidebar.selectbox("選擇行業進行掃描", industries)

# C. 原有功能
st.sidebar.subheader("🔢 手動輸入代號")
manual_s = st.sidebar.text_input("輸入股票代碼 (例: 2330,2317)", "")

# --- 4. 主畫面邏輯 ---
st.title("📊 2026 台股 AI 全能決策系統")

# 決定要分析的股票
target_stocks = []
if news_q:
    event = next((v for k, v in EVENT_DB.items() if k in news_q), None)
    if event:
        st.success(f"💡 AI 事件分析：{event['desc']}")
        target_stocks = event['stocks']
    else:
        st.warning("目前暫無此事件數據，建議嘗試輸入：『委內瑞拉』")
elif selected_ind != "請選擇":
    target_stocks = df_all[df_all['industry_category'] == selected_ind]['stock_id'].head(5).tolist()
    st.info(f"📍 行業掃描：顯示 {selected_ind} 前 5 名標的 (防止 API 限制)")
elif manual_s:
    target_stocks = [s.strip() for s in manual_s.split(",")]

# 5. 繪製與分析
if target_stocks:
    for sid in target_stocks:
        with st.container():
            hist, en_name, price = fetch_hist(sid)
            if hist.empty: continue
            
            # 獲取中文名
            cn_name = df_all[df_all['stock_id'] == sid]['stock_name'].values[0]
            
            st.subheader(f"📈 {sid} {cn_name} ({en_name})")
            c1, c2 = st.columns([3, 1])
            
            with c1:
                # K 線圖
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                fig.update_layout(height=350, margin=dict(l=0, r=0, b=0, t=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
            with c2:
                # 成交量與建議價
                v5 = int(hist['Volume'].tail(5).mean() / 1000)
                v1m = int(hist['Volume'].tail(20).mean() / 1000)
                suggest_p = round((hist['Close'].rolling(10).mean().iloc[-1] + hist['Close'].rolling(20).mean().iloc[-1])/2, 2)
                
                st.metric("即時股價", f"{price:.2f}")
                st.metric("建議買入價", f"{suggest_p:.2f}", delta_color="normal")
                
                vol_df = pd.DataFrame({
                    "週期": ["5天均量", "月均量"],
                    "張數": [v5, v1m]
                })
                st.table(vol_df)
                st.link_button("元大連結", f"https://www.yuantastock.com.tw/static/investment/stock/{sid}")
            st.divider()
else:
    st.info("👈 請由左側側邊欄開始搜尋或選擇行業。")
