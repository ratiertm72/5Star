import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup

# Generate filenames with dates
# today_str = datetime.today().strftime('%Y%m%d')
nasdaq_filename = f'nasdaq_100_info.csv'
sp500_filename = f'sp500_info.csv'

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
    
    df = pd.DataFrame(companies_info)
    df.to_csv(nasdaq_filename, index=False)  # Save to CSV with today's date
    return df

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
    
    df = pd.DataFrame(companies_info)
    df.to_csv(sp500_filename, index=False)  # Save to CSV with today's date
    return df

# Function to load stock information from CSV or fetch it if not available
def load_stock_info(index):
    if index == "NASDAQ":
        if os.path.exists(nasdaq_filename):
            return pd.read_csv(nasdaq_filename)
        else:
            return fetch_nasdaq_100_info()
    elif index == "S&P 500":
        if os.path.exists(sp500_filename):
            return pd.read_csv(sp500_filename)
        else:
            return fetch_sp500_info()
    else:
        return pd.DataFrame()

today_str = datetime.today().strftime('%Y%m%d')

# Function to load stock data from CSV or fetch it if not available
def load_stock_data(ticker, start_date, end_date):
    # Create a filename based on the ticker and date
    filename = f'{ticker}_{today_str}.csv'
    
    # Check if the file exists
    if os.path.exists(filename):
        # Load data from CSV
        data = pd.read_csv(filename, index_col='Date', parse_dates=True)
        st.write(f"Loaded data from {filename}")
    else:
        # Fetch data from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date)
        # Save the data to CSV
        if not data.empty:
            data.to_csv(filename)
            st.write(f"Saved data to {filename}")
    
    return data

# Example usage in Streamlit
st.title("Stock Data Analysis")

# Sidebar for selecting index
index = st.sidebar.selectbox("Select an index:", ["NASDAQ", "S&P 500"])

# Load the stock info dynamically based on selected index
stock_info_df = load_stock_info(index)

if not stock_info_df.empty:
    selected_company = st.sidebar.selectbox("Select a company to analyze:", stock_info_df["Ticker"].tolist())
    
    selected_info = stock_info_df[stock_info_df["Ticker"] == selected_company].iloc[0]
    ticker = selected_info["Ticker"]
    
    # Display selected company details
    st.subheader(f"Company: {selected_info['Company']} ({selected_info['Ticker']})")
    st.write(f"**Sector:** {selected_info['GICS Sector']}")
    st.write(f"**Sub-Industry:** {selected_info['GICS Sub-Industry']}")
  #  st.write(f"**Ticker:** {selected_info['Ticker']}")


    # Date selection
    start_date = st.sidebar.date_input("Start date", value=datetime(2020, 1, 1))
    end_date = st.sidebar.date_input("End date", value=datetime.today())

    # Fetch stock data from Yahoo Finance
    # Load or fetch stock data
    data = load_stock_data(ticker, start_date, end_date)

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
        st.subheader(f"일목현황표")

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

        # Adjust plot size
        fig.update_layout(
          #  title=f"Ichimoku Kinko Hyo for {selected_info['Company']} ({ticker})",
            xaxis_title='Date',
            yaxis_title='Price',
            width=1000,  # Adjust the width as needed
            height=600,  # Adjust the height as needed
            template='plotly_white',
            showlegend=True
        )
        # Show the plot
        st.plotly_chart(fig)

else:
    st.error("No stocks available for the selected index.")
