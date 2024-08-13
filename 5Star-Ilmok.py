import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# Function to fetch NASDAQ-100 tickers and company info from Wikipedia
def fetch_nasdaq_100_info():
    url = "https://en.wikipedia.org/wiki/NASDAQ-100"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})
    
    companies_info = []
    
    for row in table.findAll('tr')[1:]:
        cells = row.findAll('td')
        ticker = cells[1].text.strip().replace('.', '-')  # Replace '.' with '-' for Yahoo Finance compatibility
        company = cells[0].text.strip()
        sector = cells[2].text.strip()
        sub_industry = cells[3].text.strip() if len(cells) > 3 else 'N/A'
        
        companies_info.append({
            "Company": company,
            "Ticker": ticker,
            "GICS Sector": sector,
            "GICS Sub-Industry": sub_industry
        })
    
    return pd.DataFrame(companies_info)

# Function to fetch S&P 500 tickers and company info from Wikipedia
def fetch_sp500_info():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'constituents'})
    
    companies_info = []
    
    for row in table.findAll('tr')[1:]:
        cells = row.findAll('td')
        ticker = cells[0].text.strip().replace('.', '-')  # Replace '.' with '-' for Yahoo Finance compatibility
        company = cells[1].text.strip()
        sector = cells[3].text.strip()
        sub_industry = cells[4].text.strip()
        
        companies_info.append({
            "Company": company,
            "Ticker": ticker,
            "GICS Sector": sector,
            "GICS Sub-Industry": sub_industry
        })
    
    return pd.DataFrame(companies_info)

# Function to load stock list dynamically
def load_stock_info(index):
    if index == "NASDAQ":
        try:
            return fetch_nasdaq_100_info()
        except Exception as e:
            st.warning(f"Unable to fetch data for NASDAQ. Error: {e}")
            return pd.DataFrame({
                "Company": ["Apple Inc", "Microsoft Corporation", "Amazon.com, Inc.", "Facebook, Inc.", "Tesla, Inc."],
                "Ticker": ["AAPL", "MSFT", "AMZN", "FB", "TSLA"],
                "GICS Sector": ["Information Technology", "Information Technology", "Consumer Discretionary", "Communication Services", "Consumer Discretionary"],
                "GICS Sub-Industry": ["Technology Hardware, Storage & Peripherals", "Systems Software", "Internet & Direct Marketing Retail", "Interactive Media & Services", "Automobile Manufacturers"]
            })
    elif index == "S&P 500":
        try:
            return fetch_sp500_info()
        except Exception as e:
            st.warning(f"Unable to fetch data for S&P 500. Error: {e}")
            return pd.DataFrame({
                "Company": ["Apple Inc", "Microsoft Corporation", "Amazon.com, Inc.", "Alphabet Inc. (Class A)", "Alphabet Inc. (Class C)"],
                "Ticker": ["AAPL", "MSFT", "AMZN", "GOOGL", "GOOG"],
                "GICS Sector": ["Information Technology", "Information Technology", "Consumer Discretionary", "Communication Services", "Communication Services"],
                "GICS Sub-Industry": ["Technology Hardware, Storage & Peripherals", "Systems Software", "Internet & Direct Marketing Retail", "Interactive Media & Services", "Interactive Media & Services"]
            })
    else:
        return pd.DataFrame()

# Example usage in Streamlit
st.title("Stock Data Analysis")

# Sidebar for selecting index
index = st.sidebar.selectbox("Select an index:", ["NASDAQ", "S&P 500"])

# Load the stock info dynamically based on selected index
stock_info_df = load_stock_info(index)

if not stock_info_df.empty:
    selected_company = st.sidebar.selectbox("Select a company to analyze:", stock_info_df["Company"].tolist())
    
    selected_info = stock_info_df[stock_info_df["Company"] == selected_company].iloc[0]
    ticker = selected_info["Ticker"]
    
    # Display selected company details
    st.subheader(f"Company: {selected_info['Company']}")
    st.write(f"**Ticker:** {selected_info['Ticker']}")
    st.write(f"**GICS Sector:** {selected_info['GICS Sector']}")
    st.write(f"**GICS Sub-Industry:** {selected_info['GICS Sub-Industry']}")

    # Date selection
    start_date = st.sidebar.date_input("Start date", value=datetime(2020, 1, 1))
    end_date = st.sidebar.date_input("End date", value=datetime.today())

    # Fetch stock data from Yahoo Finance
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error(f"No data found for {ticker}. Please select another stock.")
    else:
        # Calculate Ichimoku Cloud components
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

        # Separate the data into two parts: green area and red area
        green_area = data[data['Senkou Span A'] >= data['Senkou Span B']]
        red_area = data[data['Senkou Span A'] < data['Senkou Span B']]

        # Plotly chart
        st.subheader(f"Ichimoku Kinko Hyo for {selected_info['Company']} ({ticker})")

        fig = go.Figure()

        # Add Close price trace
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close', line=dict(color='blue')))

        # Add Tenkan-sen trace
        fig.add_trace(go.Scatter(x=data.index, y=data['Tenkan-sen'], mode='lines', name='Tenkan-sen', line=dict(color='red')))

        # Add Kijun-sen trace
        fig.add_trace(go.Scatter(x=data.index, y=data['Kijun-sen'], mode='lines', name='Kijun-sen', line=dict(color='green')))

        # Add Senkou Span A trace
        fig.add_trace(go.Scatter(x=data.index, y=data['Senkou Span A'], mode='lines', name='Senkou Span A', line=dict(color='orange')))

        # Add Senkou Span B trace
        fig.add_trace(go.Scatter(x=data.index, y=data['Senkou Span B'], mode='lines', name='Senkou Span B', line=dict(color='purple')))

        # Add green filled area between Senkou Span A and B where A >= B
        fig.add_trace(go.Scatter(
            x=green_area.index,
            y=green_area['Senkou Span A'],
            fill=None,
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=green_area.index,
            y=green_area['Senkou Span B'],
            fill='tonexty',
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            fillcolor='rgba(0, 255, 0, 0.5)',  # Green color
            showlegend=False
        ))

        # Add red filled area between Senkou Span A and B where A < B
        fig.add_trace(go.Scatter(
            x=red_area.index,
            y=red_area['Senkou Span A'],
            fill=None,
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=red_area.index,
            y=red_area['Senkou Span B'],
            fill='tonexty',
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            fillcolor='rgba(255, 0, 0, 0.5)',  # Red color
            showlegend=False
        ))

        fig.update_layout(
            title=f"Ichimoku Kinko Hyo for {selected_info['Company']} ({ticker})",
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white',
            showlegend=True
        )

        # Show the plot
        st.plotly_chart(fig)

else:
    st.error("No stocks available for the selected index.")
