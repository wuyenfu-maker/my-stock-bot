import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime

# 1. 介面設定
st.set_page_config(page_title="台股 AI 實時監測系統", layout="wide")

# 2. 數據抓取函數 (串接真實 API)
def get_live_data(stock_id):
    # 即時股價與大盤 (Yahoo Finance)
    ticker = yf.Ticker(f"{stock_id}.TW")
    info = ticker.fast_info
    
    # 籌碼數據 (FinMind) - 獲取最新成交日
    api = DataLoader()
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        chip_df = api.taiwan_stock_broker_trading(stock_id=stock_id, start_date=start_date)
        # 計算最新一天的買賣超合計
        latest_date = chip_df['date'].max()
        day_chips = chip_df[chip_df['date'] == latest_date]
        net_buy_shares = day_chips['buy'].sum() - day_chips['sell'].sum()
        net_buy_vol = round(net_buy_shares / 1000, 1) # 換算成「張」
    except:
        net_buy_vol = "讀取中"

    return {
        "price": info.last_price,
        "change": ((info.last_price - info.previous_close) / info.previous_close) * 100,
        "chips": net_buy_vol,
        "name": yf.Ticker(f"{stock_id}.TW").info.get('shortName', stock_id)
    }

# --- 網頁配置 ---
st.title("🚀 台股 AI 籌碼實時選股系統")
st.info("系統已串接 Yahoo Finance (即時股價) 與 FinMind (分點籌碼數據)")

# 側邊欄：產業選擇
st.sidebar.header("🎯 監測配置")
sector = st.sidebar.selectbox("切換產業類別", ["半導體", "航運", "人工智慧", "重電/綠能"])
manual_input = st.sidebar.text_input("或手動輸入股票代號 (逗號隔開)", "2330,2317,2454")

# 決定要顯示哪些股票
sector_map = {
    "半導體": ["2330", "2454", "2303"],
    "航運": ["2603", "2609", "2615"],
    "人工智慧": ["2382", "3231", "2357"],
    "重電/綠能": ["1513", "1503", "1519"]
}
stocks_to_show = manual_input.split(",") if manual_input != "2330,2317,2454" else sector_map[sector]

# 顯示即時數據表格
st.subheader(f"📊 {sector} 產業 - 實時多因子分析")
results = []
for sid in stocks_to_show:
    with st.spinner(f'正在抓取 {sid} 的即時數據...'):
        data = get_live_data(sid.strip())
        results.append({
            "代號": sid,
            "名稱": data['name'],
            "成交價": f"{data['price']:.2f}",
            "漲跌幅": f"{data['change']:.2f}%",
            "主力買賣超 (張)": data['chips'],
            "參考連結": f"https://www.yuantastock.com.tw/static/investment/stock/{sid}"
        })

df = pd.DataFrame(results)
st.dataframe(df, use_container_width=True)

# 導入專業連結
st.markdown("---")
st.subheader("🔗 深度分析工具 (直連元大/鉅亨網)")
c1, c2, c3 = st.columns(3)
with c1: st.link_button("元大證券 - 技術分析", f"https://www.yuantastock.com.tw/static/investment/stock/{stocks_to_show[0]}")
with c2: st.link_button("鉅亨網 - 台股時事", "https://news.cnyes.com/news/cat/tw_stock")
with c3: st.link_button("證交所 - 盤後籌碼", "https://www.twse.com.tw/zh/page/trading/fund/BFI82U.html")
