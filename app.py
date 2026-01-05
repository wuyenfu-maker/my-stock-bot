import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from FinMind.data import DataLoader
import datetime

# 1. 頁面配置與資料讀取
st.set_page_config(page_title="AI 台股全能決策系統", layout="wide")
api = DataLoader()

@st.cache_data
def get_all_stock_info():
    # 抓取包含上市、上櫃、興櫃的全市場資訊
    return api.taiwan_stock_info()

stock_info_df = get_all_stock_info()

# 2. 定義新聞事件與推薦邏輯 (擴充版)
EVENT_DATABASE = {
    "委內瑞拉": {
        "impact": "地緣政治緊張推升原油需求與航運報價。關注油價受惠股與避險航運。",
        "stocks": ["1301", "1303", "6505", "2603", "2609", "6901"] # 含興櫃能源
    },
    "AI": {
        "impact": "2026 CES 展引領 AI 伺服器與半導體商機。關注龍頭廠與興櫃散熱黑馬。",
        "stocks": ["2330", "2454", "2382", "3017", "6695", "6719"]
    },
    "降息": {
        "impact": "資金成本降低，有利於金融股利差調整及高科技成長股評價回升。",
        "stocks": ["2881", "2882", "2330", "2454"]
    }
}

# 3. 核心數據處理函數 (含中英文、成交量、建議價)
def get_stock_analysis(sid):
    # 判斷後綴
    tk = yf.Ticker(f"{sid}.TW")
    try:
        if tk.fast_info.last_price is None or tk.fast_info.last_price == 0:
            tk = yf.Ticker(f"{sid}.TWO")
    except:
        tk = yf.Ticker(f"{sid}.TWO")

    hist = tk.history(period="3mo")
    if hist.empty: return None

    # 各週期成交量 (張)
    v2 = int(hist['Volume'].tail(2).mean() / 1000)
    v5 = int(hist['Volume'].tail(5).mean() / 1000)
    v10 = int(hist['Volume'].tail(10).mean() / 1000)
    v1m = int(hist['Volume'].tail(20).mean() / 1000)

    # 建議買入價 (MA10 與 MA20 中點)
    ma10 = hist['Close'].rolling(10).mean().iloc[-1]
    ma20 = hist['Close'].rolling(20).mean().iloc[-1]
    suggest_p = round((ma10 + ma20) / 2, 2)

    # 中英文名稱
    detail = stock_info_df[stock_info_df['stock_id'] == sid]
    cn_name = detail['stock_name'].values[0] if not detail.empty else "未知"
    en_name = tk.info.get('shortName', 'N/A')

    return {
        "sid": sid, "cn": cn_name, "en": en_name, "price": tk.fast_info.last_price,
        "v2": v2, "v5": v5, "v10": v10, "v1m": v1m, "suggest": suggest_p, "hist": hist
    }

# --- 4. 左側側邊欄設定 (解決您紅框處的問題) ---
st.sidebar.title("🎯 AI 智慧選股配置")

# A. 新聞事件搜尋推薦
st.sidebar.subheader("📰 新聞事件搜尋")
news_input = st.sidebar.text_input("搜尋關鍵字 (例: 委內瑞拉, AI)", "")

# B. 行業分類選擇
st.sidebar.subheader("🏭 行業分類選擇")
industry_list = sorted(stock_info_df['industry_category'].unique().tolist())
selected_industry = st.sidebar.selectbox("選擇行業進行掃描", ["請選擇"] + industry_list)

# C. 原本的代號輸入 (保留功能)
st.sidebar.subheader("🔢 手動輸入代號")
manual_input = st.sidebar.text_input("輸入股票代號 (逗號隔開)", "")

# --- 5. 主畫面呈現邏輯 ---
st.title("📈 2026 台股 AI 全能決策儀表板")

# 決定要分析的股票清單
final_stocks = []
analysis_title = "市場熱門個股掃描"

if news_input:
    matched = next((v for k, v in EVENT_DATABASE.items() if k in news_input), None)
    if matched:
        st.success(f"✅ **事件分析：** {matched['impact']}")
        final_stocks = matched['stocks']
        analysis_title = f"新聞事件推薦：{news_input}"
    else:
        st.warning("目前數據庫暫無此事件，建議嘗試『委內瑞拉』或『AI』")

elif selected_industry != "請選擇":
    final_stocks = stock_info_df[stock_info_df['industry_category'] == selected_industry]['stock_id'].head(8).tolist()
    analysis_title = f"行業掃描：{selected_industry}"

elif manual_input:
    final_stocks = [s.strip() for s in manual_input.split(",")]
    analysis_title = "自訂選股分析"

# 執行分析
if final_stocks:
    st.subheader(f"📊 {analysis_title}")
    for sid in final_stocks:
        data = get_stock_analysis(sid)
        if not data: continue
        
        with st.expander(f"🔍 {data['sid']} {data['cn']} ({data['en']}) - 詳細量價與 K 線", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                # K 線圖
                fig = go.Figure(data=[go.Candlestick(
                    x=data['hist'].index, open=data['hist']['Open'],
                    high=data['hist']['High'], low=data['hist']['Low'], close=data['hist']['Close']
                )])
                fig.update_layout(height=350, margin=dict(l=0, r=0, b=0, t=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write(f"**目前股價：** {data['price']}")
                st.write(f"**建議買入價：** :green[{data['suggest']}]")
                vol_table = pd.DataFrame({
                    "週期": ["2天均量", "5天均量", "10天均量", "月均量"],
                    "張數": [data['v2'], data['v5'], data['v10'], data['v1m']]
                })
                st.table(vol_table)
                st.link_button("前往元大技術面", f"https://www.yuantastock.com.tw/static/investment/stock/{sid}")

else:
    st.info("💡 請從左側選單選擇 **新聞事件**、**行業分類** 或 **輸入代號** 開始數據分析。")

st.markdown("---")
st.caption("數據來源：Yahoo Finance, FinMind, 台灣證券交易所。興櫃股票數據可能依市場掛牌狀況有所延遲。")
