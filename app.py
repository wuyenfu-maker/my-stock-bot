import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from FinMind.data import DataLoader
import datetime

# 1. 頁面配置與風格
st.set_page_config(page_title="AI 量價與國際局勢分析系統", layout="wide")
st.title("📊 2026 台股 AI 全能分析儀表板 (K線/量價/新聞)")

# 2. 國際局勢即時快報 (根據 2026/01 最新數據整理)
with st.expander("🌍 2026年1月 國際市場關鍵趨勢"):
    st.write("""
    - **AI 浪潮持續：** CES 2026 展覽啟動，黃仁勳演講引領半導體多頭；DeepSeek 開放源代碼推動算力需求。
    - **聯準會動態：** 市場預期降息防線鬆動，鮑爾接班人選成為 2026 焦點，美金匯率波動加劇。
    - **傳產機會：** 美國基礎建設與航運需求受全球貿易政策影響，資金開始流向高股息與循環股。
    """)

# 3. 核心數據抓取與量價計算
def get_advanced_data(sid):
    tk = yf.Ticker(f"{sid}.TW")
    # 抓取 2 個月的資料確保計算 1 個月均量沒問題
    hist = tk.history(period="2mo")
    if hist.empty: return None

    # 計算各週期成交量 (張數)
    def calc_vol(days):
        return int(hist['Volume'].tail(days).mean() / 1000)

    vol_2d = calc_vol(2)
    vol_5d = calc_vol(5)
    vol_10d = calc_vol(10)
    vol_1m = calc_vol(20) # 20個交易日約一個月

    # 籌碼數據
    api = DataLoader()
    try:
        df_chips = api.taiwan_stock_broker_trading(
            stock_id=sid, 
            start_date=(datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        )
        last_date = df_chips['date'].max()
        chips = (df_chips[df_chips['date'] == last_date]['buy'].sum() - df_chips[df_chips['date'] == last_date]['sell'].sum()) / 1000
    except:
        chips = 0

    return {
        "hist": hist, "price": tk.fast_info.last_price, "change": ((tk.fast_info.last_price / tk.fast_info.previous_close)-1)*100,
        "v2": vol_2d, "v5": vol_5d, "v10": vol_10d, "v1m": vol_1m, "chips": chips, "name": tk.info.get('shortName', sid)
    }

# 4. 側邊欄控制
st.sidebar.header("🔍 選股與分析配置")
input_ids = st.sidebar.text_input("輸入股票代碼 (例: 2330,2454,2603)", "2330,2317,2454")
stocks = [s.strip() for s in input_ids.split(",") if s.strip()]

# 5. 主畫面：K線圖與量價分析
for sid in stocks:
    data = get_advanced_data(sid)
    if not data: continue
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"{sid} {data['name']} - 交互式 K 線圖")
            # 繪製 K 線圖
            fig = go.Figure(data=[go.Candlestick(
                x=data['hist'].index,
                open=data['hist']['Open'], high=data['hist']['High'],
                low=data['hist']['Low'], close=data['hist']['Close'],
                name='K線'
            )])
            fig.update_layout(height=400, margin=dict(l=0, r=0, b=0, t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.write("### 📈 量價異動統計")
            st.metric("即時股價", f"{data['price']:.2f}", f"{data['change']:.2f}%")
            
            # 成交量表格
            vol_df = pd.DataFrame({
                "週期": ["2天均量", "5天均量", "10天均量", "1個月均量"],
                "張數": [data['v2'], data['v5'], data['v10'], data['v1m']]
            })
            st.table(vol_df)
            
            # 國際局勢自動診斷
            st.write("### 🤖 AI 國際局勢診斷")
            analysis = ""
            if "AI" in data['name'] or sid in ["2330", "2454", "2382"]:
                analysis = "✅ **受惠 CES 2026 題材：** 半導體與AI算力需求強勁，量能若突破 10 日均量可考慮加碼。"
            elif data['v2'] > data['v1m'] * 1.5:
                analysis = "🔥 **異常放量：** 短線資金湧入，結合目前美股開紅盤情緒，適合短線操作。"
            else:
                analysis = "💤 **盤整階段：** 量能平淡，建議等待聯準會下旬會議數據。"
            st.info(analysis)
    st.divider()

# 6. 整理出適合的股票 (自動篩選邏輯)
st.subheader("🌟 本週強勢篩選清單 (量價齊揚 + 國際題材)")
recommend_list = []
for sid in stocks:
    d = get_advanced_data(sid)
    if d and d['v2'] > d['v5'] and d['change'] > 0:
        recommend_list.append({"代號": sid, "理由": "量能連續升溫，契合 2026 第一季多頭行情"})

if recommend_list:
    st.success(f"目前推薦關注：{', '.join([r['代號'] for r in recommend_list])}")
    st.table(pd.DataFrame(recommend_list))
else:
    st.warning("目前暫無符合『量價齊揚』條件的個股，建議觀望。")
