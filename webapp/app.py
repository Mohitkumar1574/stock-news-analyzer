import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.news_scraper import NewsScraper
from src.scrapers.stock_data_fetcher import StockDataFetcher
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.technical_indicators import TechnicalIndicators
from src.models.predictor import StockPredictor

# Page config
st.set_page_config(
    page_title="Stock Market Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== GLOBAL CUSTOM CSS ==========
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Custom header gradient */
    .custom-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        text-align: center;
    }
    .custom-header h1 {
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .custom-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Card design */
    .card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid #f0f0f0;
        height: 100%;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0,0,0,0.1);
    }
    .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    .card-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #333;
        line-height: 1.2;
    }
    .card-delta {
        font-size: 1rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    /* Metric containers */
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9ecf2 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 50px;
        border: 1px solid #e9ecef;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 50px;
        padding: 0.5rem 1.8rem;
        font-weight: 500;
        color: #495057;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 50px;
        font-weight: 500;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 2rem;
        transition: all 0.2s;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Secondary button */
    .stButton button[kind="secondary"] {
        background: white;
        color: #667eea;
        border: 1px solid #667eea;
        box-shadow: none;
    }
    
    /* Input fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    
    /* DataFrames */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
    }
    
    /* Success/Info/Warning boxes */
    .stAlert {
        border-radius: 12px;
        border-left: 5px solid;
        padding: 1rem;
        font-weight: 500;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 10px;
        background: #f8f9fa;
        font-weight: 600;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e9ecef;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #868e96;
        font-size: 0.9rem;
        border-top: 1px solid #e9ecef;
        margin-top: 3rem;
    }
    
    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# ========== CUSTOM HEADER ==========
st.markdown("""
<div class="custom-header fade-in">
    <h1>📈 Stock Market News Analyzer</h1>
    <p>AI-powered insights for smarter investment decisions</p>
</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR NAVIGATION ==========
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
    st.title("Navigation")
    st.markdown("---")
    
    # Page selection
    page = st.radio(
        "Go to",
        ["📊 Analysis", "📁 Portfolio", "🏠 Home"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.info(
        "This application uses machine learning to analyze news sentiment "
        "and provide buy/sell recommendations for stocks."
    )
    
    st.markdown("---")
    st.markdown("### Quick Links")
    st.markdown("- [NewsAPI](https://newsapi.org)")
    st.markdown("- [Yahoo Finance](https://finance.yahoo.com)")
    
    st.markdown("---")
    st.caption("© 2026 Stock Analyzer")

# ========== PAGE ROUTING ==========
if page == "📊 Analysis":
    # Initialize components for analysis
    @st.cache_resource
    def init_components():
        return {
            'news_scraper': NewsScraper(),
            'stock_fetcher': StockDataFetcher(),
            'sentiment_analyzer': SentimentAnalyzer(),
            'predictor': StockPredictor()
        }
    
    components = init_components()
    
    # Analysis section header
    st.markdown("""
    <div class="fade-in">
        <h2 style="color: #333; margin-bottom: 1.5rem;">📊 Stock Analysis</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Input parameters in expander
    with st.expander("🔍 Input Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            company = st.text_input("Company Name", "Reliance Industries", key="company_input")
        with col2:
            symbol = st.text_input("Stock Symbol", "RELIANCE.NS", key="symbol_input").upper()
        with col3:
            days = st.slider("News Lookback Days", 1, 30, 7, key="days_input")
        
        analyze_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)
    
    # Main analysis content
    if analyze_btn:
        with st.spinner("Fetching data and analyzing..."):
            # Fetch news
            news_df = components['news_scraper'].fetch_company_news(company, days)
            
            # Mock data if no news
            if news_df.empty:
                st.warning("⚠️ No real news found. Using mock data for demonstration.")
                mock_news = []
                sources = ['Economic Times', 'Moneycontrol', 'Bloomberg', 'Reuters']
                headlines = [
                    f"{company} reports strong quarterly results",
                    f"{company} launches new product line",
                    f"Market analysts positive on {company} growth",
                    f"{company} faces regulatory hurdles",
                    f"{company} announces expansion plans"
                ]
                for i in range(min(5, days)):
                    mock_news.append({
                        'title': headlines[i % len(headlines)],
                        'description': f"Mock description for {company}",
                        'published_at': (datetime.now() - timedelta(days=i)).isoformat(),
                        'source': sources[i % len(sources)],
                        'url': 'https://example.com'
                    })
                news_df = pd.DataFrame(mock_news)
            
            # Sentiment analysis
            news_df = components['sentiment_analyzer'].analyze_dataframe(news_df)
            sentiment_summary = components['sentiment_analyzer'].get_average_sentiment(news_df)
            
            # Fetch stock data
            stock_data = components['stock_fetcher'].get_stock_data(symbol, period=f"{max(days, 30)}d")
            
            if not stock_data:
                st.error(f"❌ Could not fetch stock data for symbol {symbol}. Please check the symbol.")
            else:
                # Add technical indicators
                hist = stock_data['historical'].copy()
                if not hist.empty:
                    hist = TechnicalIndicators.add_all_indicators(hist)
                    stock_data['historical'] = hist
                
                # Prepare features for prediction
                features = components['predictor'].prepare_features(news_df, stock_data)
                
                # Simple rule-based recommendation
                avg_sentiment = sentiment_summary['avg_compound']
                day_change = stock_data['day_change']
                
                buy_score = 0.5
                if avg_sentiment > 0.1:
                    buy_score += 0.2
                elif avg_sentiment < -0.1:
                    buy_score -= 0.2
                
                if day_change < -2:
                    buy_score += 0.1
                elif day_change > 5:
                    buy_score -= 0.1
                
                if not hist.empty and 'RSI' in hist.columns:
                    latest_rsi = hist['RSI'].iloc[-1]
                    if latest_rsi < 30:
                        buy_score += 0.15
                    elif latest_rsi > 70:
                        buy_score -= 0.15
                
                buy_score = max(0, min(1, buy_score))
                recommendation = "BUY" if buy_score > 0.6 else "DON'T BUY" if buy_score < 0.4 else "HOLD"
                
                # Display metrics in cards
                st.markdown("### 📊 Key Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    delta_color = "normal" if stock_data['day_change'] >= 0 else "inverse"
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Current Price</div>
                        <div class="card-value">₹{stock_data['current_price']:.2f}</div>
                        <div class="card-delta" style="color: {'green' if stock_data['day_change']>0 else 'red'};">
                            {stock_data['day_change']:+.2f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    market_cap_str = f"₹{stock_data['market_cap']/1e7:.2f}Cr" if stock_data.get('market_cap') else "N/A"
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Market Cap</div>
                        <div class="card-value">{market_cap_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    sentiment_color = "green" if sentiment_summary['avg_class'] == "Positive" else "red" if sentiment_summary['avg_class'] == "Negative" else "orange"
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Avg Sentiment</div>
                        <div class="card-value">{sentiment_summary['avg_compound']:.2f}</div>
                        <div class="card-delta" style="color: {sentiment_color};">{sentiment_summary['avg_class']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    rec_color = "green" if recommendation == "BUY" else "red" if recommendation == "DON'T BUY" else "orange"
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-title">Recommendation</div>
                        <div class="card-value" style="font-size: 1.8rem;">{recommendation}</div>
                        <div class="card-delta" style="color: {rec_color};">{buy_score*100:.1f}% confidence</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Recommendation box
                if recommendation == "BUY":
                    st.success(f"✅ **RECOMMENDATION: BUY** with {buy_score*100:.1f}% confidence")
                elif recommendation == "DON'T BUY":
                    st.error(f"❌ **RECOMMENDATION: DON'T BUY** with {(1-buy_score)*100:.1f}% confidence")
                else:
                    st.warning(f"⚠️ **RECOMMENDATION: HOLD** - Market sentiment is neutral")
                
                # Tabs for detailed analysis
                tab1, tab2, tab3, tab4 = st.tabs(["📰 News", "📊 Chart", "📈 Technical", "🔮 Prediction"])
                
                with tab1:
                    st.subheader(f"Recent News about {company}")
                    st.write(f"Total articles analyzed: {len(news_df)}")
                    
                    # Sentiment pie chart
                    fig = go.Figure(data=[go.Pie(
                        labels=['Positive', 'Negative', 'Neutral'],
                        values=[sentiment_summary['positive_pct'], 
                                sentiment_summary['negative_pct'], 
                                sentiment_summary['neutral_pct']],
                        hole=.3,
                        marker_colors=['green', 'red', 'gray']
                    )])
                    fig.update_layout(title="Sentiment Distribution", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # News table
                    if not news_df.empty:
                        display_cols = ['published_at', 'source', 'title', 'sentiment_class', 'vader_compound']
                        display_df = news_df[display_cols].copy()
                        display_df.columns = ['Date', 'Source', 'Title', 'Sentiment', 'Score']
                        display_df = display_df.sort_values('Date', ascending=False).head(10)
                        
                        def color_sentiment(val):
                            if val == 'Positive':
                                return 'background-color: #d4edda'
                            elif val == 'Negative':
                                return 'background-color: #f8d7da'
                            else:
                                return 'background-color: #fff3cd'
                        
                        styled_df = display_df.style.map(color_sentiment, subset=['Sentiment'])
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                with tab2:
                    st.subheader(f"{symbol} Stock Price - Last {days} Days")
                    
                    if not hist.empty:
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                           vertical_spacing=0.03, row_heights=[0.7, 0.3])
                        
                        fig.add_trace(go.Candlestick(
                            x=hist.index.strftime('%Y-%m-%d'),
                            open=hist['Open'],
                            high=hist['High'],
                            low=hist['Low'],
                            close=hist['Close'],
                            name="Price",
                            increasing_line_color='green',
                            decreasing_line_color='red'
                        ), row=1, col=1)
                        
                        fig.add_trace(go.Bar(
                            x=hist.index.strftime('%Y-%m-%d'),
                            y=hist['Volume'],
                            name="Volume",
                            marker_color='lightblue'
                        ), row=2, col=1)
                        
                        fig.update_layout(
                            title=f"{symbol} Stock Price",
                            xaxis_title="Date",
                            yaxis_title="Price (₹)",
                            xaxis_rangeslider_visible=False,
                            height=600
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Last price highlight
                        last_price = hist['Close'].iloc[-1]
                        last_date = hist.index[-1].strftime('%Y-%m-%d')
                        st.info(f"📌 Last Price: ₹{last_price:.2f} as of {last_date}")
                    else:
                        st.warning("No historical data available for chart")
                
                with tab3:
                    st.subheader("Technical Indicators")
                    
                    if not hist.empty:
                        # RSI
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(
                            x=hist.index.strftime('%Y-%m-%d'), y=hist['RSI'],
                            mode='lines', name='RSI', line=dict(color='purple')
                        ))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                        fig_rsi.update_layout(title="RSI", height=300)
                        st.plotly_chart(fig_rsi, use_container_width=True)
                        
                        # MACD
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(
                            x=hist.index.strftime('%Y-%m-%d'), y=hist['MACD'],
                            mode='lines', name='MACD', line=dict(color='blue')
                        ))
                        fig_macd.add_trace(go.Scatter(
                            x=hist.index.strftime('%Y-%m-%d'), y=hist['Signal'],
                            mode='lines', name='Signal', line=dict(color='red')
                        ))
                        fig_macd.update_layout(title="MACD", height=300)
                        st.plotly_chart(fig_macd, use_container_width=True)
                        
                        # Moving Averages
                        fig_ma = go.Figure()
                        fig_ma.add_trace(go.Scatter(
                            x=hist.index.strftime('%Y-%m-%d'), y=hist['Close'],
                            mode='lines', name='Close', line=dict(color='black', width=2)
                        ))
                        fig_ma.add_trace(go.Scatter(
                            x=hist.index.strftime('%Y-%m-%d'), y=hist['MA20'],
                            mode='lines', name='MA20', line=dict(color='blue', dash='dash')
                        ))
                        fig_ma.add_trace(go.Scatter(
                            x=hist.index.strftime('%Y-%m-%d'), y=hist['MA50'],
                            mode='lines', name='MA50', line=dict(color='orange', dash='dash')
                        ))
                        fig_ma.update_layout(title="Moving Averages", height=300)
                        st.plotly_chart(fig_ma, use_container_width=True)
                    else:
                        st.warning("No historical data for technical indicators")
                
                with tab4:
                    st.subheader("Prediction Details")
                    
                    if components['predictor'].feature_names:
                        feature_df = pd.DataFrame({
                            'Feature': components['predictor'].feature_names,
                            'Value': features.flatten()
                        })
                        st.dataframe(feature_df, use_container_width=True, hide_index=True)
                    
                    st.markdown("**How it works:**")
                    st.info(
                        "The prediction combines:\n"
                        "- 📰 News sentiment\n"
                        "- 📈 Price change\n"
                        "- 📊 Trading volume\n"
                        "- 💹 P/E ratio\n"
                        "- 📉 Short-term trend\n"
                        "- 📊 Volatility\n\n"
                        "Score > 0.6 = BUY, Score < 0.4 = DON'T BUY, in between = HOLD"
                    )
                    
                    if recommendation == "BUY":
                        st.balloons()
    
    # If not analyzed yet
    else:
        st.info("👆 Enter parameters and click **Analyze Stock** to get started.")

elif page == "📁 Portfolio":
    # Import and show portfolio page
    from pages.portfolio import show_portfolio
    show_portfolio()

elif page == "🏠 Home":
    # Import and show home page
    from pages.home import show_home
    show_home()