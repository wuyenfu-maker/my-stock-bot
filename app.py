import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from FinMind.data import DataLoader
import datetime

# 1. 頁面初始化與快取
st.set_page_config(page_title="AI 智慧事件選股系統", layout="wide")
api = DataLoader()

@st.cache_data
def get_all_stock_info():
    # 抓取全市場股票資訊（含興櫃、上市、上櫃）
    return api.taiwan_stock_info()

stock_info_df = get_all_stock_info()

# 2. 定義時事與股票推薦邏輯 (智慧映射庫)
EVENT_MAP = {
    "委內瑞拉": {
        "reason": "委內瑞拉地緣政治動盪推升油價，對塑化及航運避險有直接影響。",
        "stocks": ["1301", "1303", "6505", "2603", "2609"]
    },
    "AI/輝達/CES": {
        "reason": "2026 CES 展引發算力升級潮，半導體與 AI 伺服器代工廠為核心受惠者。",
        "stocks": ["2330", "2454", "2382", "3231", "3017"]
    },
    "軍工/地緣緊張": {
        "reason": "全球地緣政治局勢緊張，帶動無人機與防衛系統需求。",
        "stocks": ["2634", "8033", "2645", "5222"] # 包含興櫃/上櫃潛力股
    }
}

# 3. 數據抓取與分析函數
def analyze_stock(sid):
    # 判斷後綴 (上市 .TW, 上櫃/興櫃 .TWO)
    tk = yf.Ticker(f"{sid}.TW")
    try:
        if tk.fast_info.last_price is None or tk.fast_info.last_price == 0:
            tk = yf.Ticker(f"{sid}.TWO")
    except:
        tk = yf.Ticker(f"{sid}.TWO")

    hist = tk.history(period="3mo")
    if hist.empty: return None

    # 成交量分析 (張數)
    vol_5d = int(hist['Volume'].tail(5).mean() / 1000)
    vol_10d = int(hist['Volume'].tail(10).mean() / 1000)
    vol_1m = int(hist['Volume'].tail(20).mean() / 1000)

    # 建議購買價：MA10 與 MA20 的中點 (回測支撐位)
    ma10 = hist['Close'].rolling(10).mean().iloc[-1]
    ma20 = hist['Close'].rolling(20).mean().iloc[-1]
    suggest_price = round((ma10 + ma20) / 2, 2)

    # 獲取中英文名稱
    stock_detail = stock_info_df[stock_info_df['stock_id'] == sid]
    ch_name = stock_detail['stock_name'].values[0] if not stock_detail.empty else "未知"
    en_name = tk.info.get('shortName', 'N/A')

    return {
        "代號": sid, "中文名": ch_name, "英文名": en_name,
        "現價": tk.fast_info.last_price, "5日均量": vol_5d,
        "10日均量": vol_10d, "月均量": vol_1m,
        "建議買入價": suggest_price, "狀態": "量增" if vol_5d > vol_1m else "盤整"
    }

# --- 4. 左側側邊欄設定 ---
st.sidebar.title("🎯 投資決策中心")

# 新聞事件搜尋推薦
st.sidebar.subheader("📰 時事事件推薦")
news_query = st.sidebar.text_input("搜尋新聞關鍵字 (如: 委內瑞拉, AI, 輝達)", "")

# 行業分類選擇
st.sidebar.subheader("🏭 行業分類選擇")
all_sectors = sorted(stock_info_df['industry_category'].unique().tolist())
selected_sector = st.sidebar.selectbox("選擇特定行業進行掃描", ["請選擇"] + all_sectors)

# --- 5. 主畫面邏輯 ---
st.title("🚀 AI 台股事件分析與行業掃描儀表板")

# 處理「時事搜尋」
if news_query:
    st.markdown(f"### 🔍 新聞事件分析：{news_query}")
    matched_event = next((v for k, v in EVENT_MAP.items() if any(sub in news_query for sub in k.split("/"))), None)
    
    if matched_event:
        st.info(f"💡 **AI 邏輯：** {matched_event['reason']}")
        results = []
        for sid in matched_event['stocks']:
            data = analyze_stock(sid)
            if data: results.append(data)
        st.table(pd.DataFrame(results))
    else:
        st.warning("目前數據庫暫無此事件的關聯推薦，建議嘗試：『委內瑞拉』、『AI』、『軍工』。")

# 處理「行業分類」
elif selected_sector != "請選擇":
    st.markdown(f"### 🏭 行業深度掃描：{selected_sector}")
    sector_stocks = stock_info_df[stock_info_df['industry_category'] == selected_sector].head(10) # 顯示前10大
    
    sector_results = []
    for sid in sector_stocks['stock_id'].tolist():
        data = analyze_stock(sid)
        if data: sector_results.append(data)
    
    st.dataframe(pd.DataFrame(sector_results), use_container_width=True)

else:
    st.write("請從左側側邊欄 **輸入新聞關鍵字** 或 **選擇行業分類** 開始分析。")
    # 預設展示熱門個股 K 線
    st.divider()
    st.subheader("🔥 今日市場關注個股 (K線)")
    demo_sid = "2330"
    tk_demo = yf.Ticker(f"{demo_sid}.TW")
    h = tk_demo.history(period="3mo")
    fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
    fig.update_layout(title=f"{demo_sid} 台積電 實時K線圖", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("數據來源：Yahoo Finance, FinMind, 台灣證券交易所。AI 建議價格僅供參考。")
