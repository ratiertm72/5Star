import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# "5-star stocks rated by CFRA" 목록
stocks = {
    "ARCH CAPITAL GROUP LTD": "ACGL",
    "ACCENTURE PLC": "ACN",
    "AERCAP HOLDINGS NV": "AER",
    "ARISTA NETWORKS INC": "ANET",
    "AIR PRODUCTS & CHEMICALS INC": "APD",
    "APTIV PLC": "APTV",
    "ALEXANDRIA R E EQUITIES INC": "ARE",
    "ASML HOLDING NV": "ASML",
    "ASTRAZENECA PLC": "AZN",
    "BALL CORP": "BALL",
    "CACI INTL INC -CL A": "CACI",
    "CBOE GLOBAL MARKETS INC": "CBOE",
    "CLEAN HARBORS INC": "CLH",
    "SALESFORCE INC": "CRM",
    "CROCS INC": "CROX",
    "CARPENTER TECHNOLOGY CORP": "CRS",
    "CYBERARK SOFTWARE LTD": "CYBR",
    "EQUIFAX INC": "EFX",
    "EATON CORP PLC": "ETN",
    "EAST WEST BANCORP INC": "EWBC",
    "FREEPORT-MCMORAN INC": "FCX",
    "FLOWSERVE CORP": "FLS",
    "FEDERAL REALTY INVESTMENT TR": "FRT",
    "GUARDANT HEALTH INC": "GH",
    "GOODYEAR TIRE & RUBBER CO": "GT",
    "CHART INDUSTRIES INC": "GTLS",
    "INTERACTIVE BROKERS GROUP": "IBKR",
    "LILLY (ELI) & CO": "LLY",
    "LULULEMON ATHLETICA INC": "LULU",
    "MCCORMICK & CO INC": "MKC",
    "MP MATERIALS CORP": "MP",
    "MARVELL TECHNOLOGY INC": "MRVL",
    "MICROSOFT CORP": "MSFT",
    "M & T BANK CORP": "MTB",
    "NATIONAL BANK CANADA": "NA",
    "NEWMONT CORP": "NEM",
    "SERVICENOW INC": "NOW",
    "ORANGE": "ORAN",
    "PNC FINANCIAL SVCS GROUP INC": "PNC",
    "PURE STORAGE INC": "PSTG",
    "PATTERSON-UTI ENERGY INC": "PTEN",
    "SCHWAB (CHARLES) CORP": "SCHW",
    "CONSTELLATION BRANDS": "STZ",
    "SUMMIT MATERIALS INC": "SUM",
    "MOLSON COORS BEVERAGE CO": "TAP",
    "TECK RESOURCES LTD": "TECK",
    "T-MOBILE US INC": "TMUS",
    "VISTEON CORP": "VC",
    "VERTIV HOLDINGS CO": "VRT",
    "XYLEM INC": "XYL"
}

# Streamlit 설정
st.title("5-Star Stocks Rated by CFRA - Ichimoku Kinko Hyo")

# 사이드바 설정
selected_stock = st.sidebar.selectbox("Select a stock to analyze:", list(stocks.keys()))
ticker = stocks[selected_stock]

# 날짜 선택
start_date = st.sidebar.date_input("Start date", value=datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End date", value=datetime.today())

# Yahoo Finance에서 데이터 가져오기
data = yf.download(ticker, start=start_date, end=end_date)

# 일목균형표 계산
def calculate_ichimoku(data):
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    data['Tenkan-sen'] = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    data['Kijun-sen'] = (high_26 + low_26) / 2

    data['Senkou Span A'] = ((data['Tenkan-sen'] + data['Kijun-sen']) / 2).shift(26)
    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    data['Senkou Span B'] = ((high_52 + low_52) / 2).shift(26)

    data['Chikou Span'] = data['Close'].shift(-26)
    return data

data = calculate_ichimoku(data)

# 차트 그리기
st.subheader(f"Ichimoku Kinko Hyo for {selected_stock} ({ticker})")
plt.figure(figsize=(14, 9))
plt.plot(data.index, data['Close'], label='Close', color='blue')
plt.plot(data.index, data['Tenkan-sen'], label='Tenkan-sen', color='red')
plt.plot(data.index, data['Kijun-sen'], label='Kijun-sen', color='blue')
plt.fill_between(data.index, data['Senkou Span A'], data['Senkou Span B'], where=data['Senkou Span A'] >= data['Senkou Span B'], color='green', alpha=0.5)
plt.fill_between(data.index, data['Senkou Span A'], data['Senkou Span B'], where=data['Senkou Span A'] < data['Senkou Span B'], color='red', alpha=0.5)
plt.plot(data.index, data['Chikou Span'], label='Chikou Span', color='purple')
plt.legend()
plt.title(f"Ichimoku Kinko Hyo for {selected_stock} ({ticker})")
st.pyplot(plt)
