import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def show_home():
    st.title("🏠 Home")
    
    st.markdown("""
    ## Welcome to Stock Market News Analyzer!
    
    This application helps you make informed investment decisions by analyzing:
    
    - **News Sentiment**: Uses NLP to gauge market sentiment from recent news
    - **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands
    - **Price Action**: Current price, daily change, and historical trends
    - **Machine Learning**: Combines all factors to give buy/sell recommendations
    
    ### 📊 Features:
    
    - **Real-time News Scraping**: Fetches latest news about companies
    - **Sentiment Analysis**: Analyzes news sentiment using VADER and TextBlob
    - **Stock Data**: Fetches live and historical stock data from Yahoo Finance
    - **Technical Analysis**: Calculates RSI, MACD, Moving Averages automatically
    - **Recommendations**: Get BUY/HOLD/DON'T BUY recommendations
    
    ### 🚀 How to Use:
    
    1. Go to **Analysis** page from sidebar
    2. Enter company name and stock symbol
    3. Select number of days for news lookback
    4. Click "Analyze Stock" button
    5. View results across different tabs
    
    ### 📝 Example:
    
    - **Company**: Reliance Industries
    - **Symbol**: RELIANCE.NS (for NSE) or RELIANCE.BO (for BSE)
    
    ### ⚠️ Disclaimer:
    
    This is for educational purposes only. Always do your own research before investing.
    """)
    
    # Quick stats or info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📰 **News Analysis**\n\nSentiment analysis of latest news articles")
    with col2:
        st.info("📊 **Technical Indicators**\n\nRSI, MACD, Moving Averages")
    with col3:
        st.info("🤖 **ML Predictions**\n\nBuy/Sell recommendations")

if __name__ == "__main__":
    show_home()
else:
    show_home()