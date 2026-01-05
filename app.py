import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime

# 1. 頁面配置
st.set_page_config(page_title="AI 事件驅動選股系統", layout="wide")
st.title("🤖 AI 投資決策機器人：事件分析與選股")

# 2. 定義「事件與產業」關聯邏輯 (AI 知識庫)
# 這裡模擬 AI 的判斷邏輯，實務上可串接 LLM API
def ai_event_analyzer(keyword):
    analysis = {
        "委瑞內拉": {
            "sectors": ["塑膠/石油", "航運", "軍工"],
            "stocks": ["1301", "1303", "2603", "2634"],
            "impact": "委瑞內拉為原油大國，地緣政治動盪將推升油價，對台塑三寶有利；避險需求可能帶動航運報價。"
        },
        "CES": {
            "sectors": ["AI伺服器", "散熱", "半導體"],
            "stocks": ["2330", "2382", "3017", "2454"],
            "impact": "2026 CES 展點燃 AI 算力需求，散熱與伺服器代工廠為直接受惠者。"
        },
        "降息": {
            "sectors": ["金融", "資產股", "科技成長股"],
            "stocks": ["2881", "2882", "2330"],
            "impact": "降息有利於銀行利差調整及高科技股評價提升。"
        }
    }
    # 搜尋關鍵字匹配
    for key in analysis:
        if key in keyword:
            return analysis[key]
    return None

# 3. 價格建議邏輯 (簡單技術面支撐計算)
def get_recommendation(sid):
    tk = yf.Ticker(f"{sid}.TW")
    hist = tk.history(period="1mo")
    curr_price = tk.fast_info.last_price
    
    # 建議購買價：設在 5 日線與 10 日線之間 (分批佈局位)
    ma5 = hist['Close'].rolling(5).mean().iloc[-1]
    ma10 = hist['Close'].rolling(10).mean().iloc[-1]
    suggest_price = (ma5 + ma10) / 2
    
    return {
        "name": tk.info.get('shortName', sid),
        "curr": curr_price,
        "suggest": round(suggest_price, 2),
        "diff": round(((suggest_price / curr_price) - 1) * 100, 2)
    }

# --- 主介面 ---
st.markdown("### 🔍 第一步：輸入時事關鍵字")
keyword = st.text_input("輸入近期國際新聞或事件（例如：委瑞內拉總統、AI伺服器需求、CES 2026）", placeholder="請輸入關鍵字...")

if keyword:
    event_result = ai_event_analyzer(keyword)
    
    if event_result:
        st.success(f"✅ **AI 分析結果：** {event_result['impact']}")
        
        st.markdown("### 📈 第二步：受惠股票分析與購買建議")
        recommend_data = []
        for sid in event_result['stocks']:
            with st.spinner(f"正在計算 {sid} 的最佳切入點..."):
                rec = get_recommendation(sid)
                recommend_data.append({
                    "股票代號": sid,
                    "名稱": rec['name'],
                    "目前股價": rec['curr'],
                    "建議買入價 (參考支撐)": rec['suggest'],
                    "與現價差距": f"{rec['diff']}%",
                    "操作建議": "分批低接" if rec['diff'] < 0 else "強勢突破中"
                })
        
        st.table(pd.DataFrame(recommend_data))
        
        # 額外提供元大與即時量價 K 線
        selected_sid = st.selectbox("選擇個股查看 K 線圖", event_result['stocks'])
        # (這裡可以放入上一版本的 Plotly K 線程式碼...)
        st.link_button(f"前往元大證券查看 {selected_sid} 深度報告", f"https://www.yuantastock.com.tw/static/investment/stock/{selected_sid}")
        
    else:
        st.warning("目前 AI 庫中暫無此事件的關聯數據，請嘗試其他關鍵字（如：石油、AI、降息）。")

st.markdown("---")
st.caption("⚠️ 免責聲明：本網站所有數據及 AI 建議僅供參考，不代表投資要約，投資請自行評估風險。")
