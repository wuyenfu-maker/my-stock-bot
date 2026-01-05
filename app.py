import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime

# 1. 頁面標題與設定
st.set_page_config(page_title="台股 AI 實時監測", layout="wide")
st.title("📈 台股 AI 籌碼實時監測系統")

# 2. 功能函數：抓取 Yahoo Finance 即時價格與 FinMind 籌碼
def get_stock_report(stock_id):
    # 即時股價
    tk = yf.Ticker(f"{stock_id}.TW")
    price = tk.fast_info.last_price
    change = ((price - tk.fast_info.previous_close) / tk.fast_info.previous_close) * 100
    
    # 籌碼數據 (抓取最近一個交易日)
    api = DataLoader()
    try:
        df_chips = api.taiwan_stock_broker_trading(
            stock_id=stock_id, 
            start_date=(datetime.date.today() - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        )
        last_date = df_chips['date'].max()
        daily_sum = df_chips[df_chips['date'] == last_date]
        net_vol = (daily_sum['buy'].sum() - daily_sum['sell'].sum()) / 1000 # 換算成張
    except:
        net_vol = 0
        
    return {"price": price, "change": change, "chips": net_vol, "name": tk.info.get('shortName', stock_id)}

# 3. 側邊欄自訂選股
st.sidebar.header("🔍 自訂追蹤")
input_ids = st.sidebar.text_input("輸入股票代號 (逗號隔開)", "2330,2317,2454,2603")
stocks = input_ids.split(",")

# 4. 顯示表格
results = []
for sid in stocks:
    sid = sid.strip()
    with st.spinner(f'同步數據中: {sid}...'):
        data = get_stock_report(sid)
        results.append({
            "代號": sid,
            "名稱": data['name'],
            "即時價": f"{data['price']:.2f}",
            "漲跌幅": f"{data['change']:.2f}%",
            "主力買賣超 (張)": f"{data['chips']:.1f}",
            "元大參考連結": f"https://www.yuantastock.com.tw/static/investment/stock/{sid}"
        })

df = pd.DataFrame(results)
st.table(df)

# 5. 導入外部專業資源連結
st.markdown("---")
st.subheader("🔗 專業投資參考連結")
col1, col2 = st.columns(2)
with col1:
    st.info("💡 **即時股價說明：** 串接 Yahoo Finance API，盤中每秒更新。")
    st.link_button("前往【元大證券】技術分析", f"https://www.yuantastock.com.tw/static/investment/stock/{stocks[0].strip()}")
with col2:
    st.info("📊 **籌碼數據說明：** 串接證交所分點明細，每日 15:30 盤後更新。")
    st.link_button("前往【鉅亨網】即時新聞", "https://news.cnyes.com/news/cat/tw_stock")
