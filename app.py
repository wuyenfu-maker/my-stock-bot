import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime

# 1. 網頁設定
st.set_page_config(page_title="台股 AI 實時監測", layout="wide")

# 2. 初始化數據抓取器 (使用 FinMind 抓取台股籌碼)
api = DataLoader()

def get_real_time_data(stock_id):
    # 抓取即時股價 (Yahoo Finance)
    ticker = yf.Ticker(f"{stock_id}.TW")
    info = ticker.info
    hist = ticker.history(period="5d")
    
    # 抓取券商籌碼 (FinMind) - 取最近一個交易日
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
    
    try:
        # 抓取券商買賣超資料
        chip_df = api.taiwan_stock_broker_trading(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
        # 計算前五大券商買賣超合計
        net_buy = chip_df.groupby('broker_name')['buy'].sum().sum() - chip_df.groupby('broker_name')['sell'].sum().sum()
    except:
        net_buy = 0  # 萬一 API 沒資料時的防錯

    return {
        "price": info.get('regularMarketPrice', hist['Close'].iloc[-1]),
        "change": info.get('regularMarketChangePercent', 0),
        "net_buy": net_buy,
        "name": info.get('shortName', '未知')
    }

# --- 介面開始 ---
st.title("📊 台股實時籌碼選股機器人")
st.caption("數據源：Yahoo Finance / 證交所 / FinMind (每日盤後更新)")

# 側邊欄：產業與個股手動輸入
st.sidebar.header("🎯 追蹤設定")
target_stocks = st.sidebar.text_input("輸入股票代號 (以逗號隔開)", "2330,2317,2603,1513")
stock_list = target_stocks.split(",")

# 頂部大盤動態 (台指)
with st.spinner('正在獲取最新數據...'):
    taiex = yf.Ticker("^TWII").history(period="1d")
    current_taiex = taiex['Close'].iloc[-1]
    taiex_change = ((current_taiex - taiex['Open'].iloc[-1]) / taiex['Open'].iloc[-1]) * 100

col1, col2 = st.columns(2)
col1.metric("加權指數 (TAIEX)", f"{current_taiex:.2f}", f"{taiex_change:.2f}%")
col2.info("💡 籌碼說明：券商買賣超數據於每日 15:30 盤後更新，股價為即時更新。")

# 數據展示
st.subheader("📋 個股多因子分析表")
final_results = []

for sid in stock_list:
    try:
        res = get_real_time_data(sid.strip())
        final_results.append({
            "代號": sid,
            "名稱": res['name'],
            "現價": f"{res['price']:.2f}",
            "漲跌幅": f"{res['change']:.2f}%",
            "主力買賣超(張)": int(res['net_buy'] / 1000), # 換算成張
            "狀態": "偏多" if res['net_buy'] > 0 else "偏空"
        })
    except:
        continue

df_display = pd.DataFrame(final_results)
st.table(df_display)

# 模擬時事新聞連結
st.markdown("---")
st.subheader("📰 相關投資參考連結")
st.write(f"[查看 {stock_list[0]} 元大證券技術面](https://www.yuantastock.com.tw/static/investment/stock/{stock_list[0]})")
st.write("[查看鉅亨網台股頭條](https://news.cnyes.com/news/cat/tw_stock)")
