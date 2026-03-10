import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.scrapers.news_scraper import NewsScraper
from src.scrapers.stock_data_fetcher import StockDataFetcher
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.technical_indicators import TechnicalIndicators
from src.models.predictor import StockPredictor

# FORCE CACHE CLEAR - DELETE THIS LINE

def show_analysis():
    st.markdown("""
    <div class="fade-in">
        <h2 style="color: #333; margin-bottom: 1.5rem;">📊 Stock Analysis</h2>
    </div>
    """, unsafe_allow_html=True)
    
    @st.cache_resource
    def init_components():
        return {
            'news_scraper': NewsScraper(),
            'stock_fetcher': StockDataFetcher(),
            'sentiment_analyzer': SentimentAnalyzer(),
            'predictor': StockPredictor()
        }
    
    components = init_components()
    
    with st.expander("🔍 Input Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            company = st.text_input("Company Name", "Reliance Industries", key="analysis_company")
        with col2:
            symbol = st.text_input("Stock Symbol", "RELIANCE.NS", key="analysis_symbol").upper()
        with col3:
            days = st.slider("News Lookback Days", 1, 30, 7, key="analysis_days")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)
    
    if analyze_btn:
        with st.spinner("Fetching data and analyzing..."):
            news_df = components['news_scraper'].fetch_company_news(company, days)
            
            if news_df.empty:
                st.warning("⚠️ No real news found. Using mock data.")
                mock_news = []
                sources = ['Economic Times', 'Moneycontrol', 'Bloomberg', 'Reuters']
                headlines = [
                    f"{company} Q3 results",
                    f"{company} announces partnership",
                    f"Analysts review {company}",
                    f"{company} market update",
                    f"{company} industry outlook"
                ]
                
                for i in range(min(3, days)):
                    random_sentiment = round(np.random.uniform(-0.2, 0.2), 2)
                    sent_class = 'Positive' if random_sentiment > 0.05 else 'Negative' if random_sentiment < -0.05 else 'Neutral'
                    
                    mock_news.append({
                        'title': f"{headlines[i % len(headlines)]} - {datetime.now().strftime('%d %b')}",
                        'published_at': (datetime.now() - timedelta(days=i)).isoformat(),
                        'source': sources[i % len(sources)],
                        'vader_compound': random_sentiment,
                        'sentiment_class': sent_class
                    })
                news_df = pd.DataFrame(mock_news)
            
            if 'vader_compound' not in news_df.columns:
                news_df = components['sentiment_analyzer'].analyze_dataframe(news_df)
            
            sentiment_summary = components['sentiment_analyzer'].get_average_sentiment(news_df)
            stock_data = components['stock_fetcher'].get_stock_data(symbol, period=f"{max(days, 30)}d")
            
            if not stock_data:
                st.error(f"❌ Could not fetch stock data for symbol {symbol}.")
                return
            
            hist = stock_data['historical'].copy()
            if not hist.empty:
                hist = TechnicalIndicators.add_all_indicators(hist)
                stock_data['historical'] = hist
            
            features = components['predictor'].prepare_features(news_df, stock_data)
            
            avg_sentiment = sentiment_summary['avg_compound']
            day_change = stock_data['day_change']
            
            latest_rsi = None
            if not hist.empty and 'RSI' in hist.columns and not hist['RSI'].empty:
                latest_rsi = hist['RSI'].iloc[-1]
            
            # ===== PRICE-BASED LOGIC (FINAL) =====
            if day_change > 1.0:
                base = 0.7
            elif day_change < -0.5:
                base = 0.3
            else:
                base = 0.5
            
            sent_adj = 0.05 if avg_sentiment > 0.2 else (-0.05 if avg_sentiment < -0.2 else 0)
            rsi_adj = 0.05 if latest_rsi and latest_rsi < 30 else (-0.05 if latest_rsi and latest_rsi > 70 else 0)
            
            buy_score = base + sent_adj + rsi_adj
            buy_score = max(0.2, min(0.8, buy_score))
            
            recommendation = "BUY" if buy_score > 0.6 else "DON'T BUY" if buy_score < 0.4 else "HOLD"
            
            # ========== DEBUG INFO ==========
            st.markdown("### 🔍 Debug Info")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Sentiment:** {avg_sentiment:.2f} → {sent_adj:+.2f}")
            with col2:
                base_label = ">1%" if day_change > 1.0 else "<-0.5%" if day_change < -0.5 else "between"
                st.markdown(f"**Day Change:** {day_change:.2f}% ({base_label}) → Base: {base}")
            with col3:
                st.markdown(f"**RSI:** {latest_rsi if latest_rsi else 'N/A'} → {rsi_adj:+.2f}")
            
            st.markdown(f"**Final Score:** {buy_score:.2f} → **{recommendation}**")
            
            # ========== METRICS CARDS ==========
            st.markdown("### 📊 Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                delta_color = "green" if stock_data['day_change'] >= 0 else "red"
                st.metric("Current Price", f"₹{stock_data['current_price']:.2f}", f"{stock_data['day_change']:+.2f}%")
            with col2:
                market_cap_str = f"₹{stock_data['market_cap']/1e7:.2f}Cr" if stock_data.get('market_cap') else "N/A"
                st.metric("Market Cap", market_cap_str)
            with col3:
                st.metric("Avg Sentiment", f"{sentiment_summary['avg_compound']:.2f}", sentiment_summary['avg_class'])
            with col4:
                st.metric("Recommendation", recommendation, f"{buy_score*100:.1f}%")
            
            if recommendation == "BUY":
                st.success(f"✅ **RECOMMENDATION: BUY** with {buy_score*100:.1f}% confidence")
            elif recommendation == "DON'T BUY":
                st.error(f"❌ **RECOMMENDATION: DON'T BUY** with {(1-buy_score)*100:.1f}% confidence")
            else:
                st.warning(f"⚠️ **RECOMMENDATION: HOLD** - Score: {buy_score:.2f}")
            
            # ========== TABS ==========
            tab1, tab2, tab3, tab4 = st.tabs(["📰 News", "📊 Chart", "📈 Technical", "🔮 Prediction"])
            
            with tab1:
                st.subheader(f"📰 Recent News about {company}")
                st.write(f"Articles: {len(news_df)}")
                if not news_df.empty:
                    st.dataframe(news_df[['published_at', 'source', 'title', 'sentiment_class', 'vader_compound']].head(10), use_container_width=True)
            
            with tab2:
                st.subheader(f"{symbol} Stock Price")
                if not hist.empty:
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                    fig.add_trace(go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                        name="Price", increasing_line_color='#28a745', decreasing_line_color='#dc3545'
                    ), row=1, col=1)
                    fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name="Volume", marker_color='#17a2b8'), row=2, col=1)
                    fig.update_layout(height=600, xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No historical data")
            
            with tab3:
                st.subheader("Technical Indicators")
                if not hist.empty:
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                    fig_rsi.update_layout(title="RSI (14)", height=300)
                    st.plotly_chart(fig_rsi, use_container_width=True)
                    
                    if 'MACD' in hist.columns:
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(x=hist.index, y=hist['MACD'], mode='lines', name='MACD', line=dict(color='blue')))
                        fig_macd.add_trace(go.Scatter(x=hist.index, y=hist['Signal'], mode='lines', name='Signal', line=dict(color='red')))
                        fig_macd.update_layout(title="MACD", height=300)
                        st.plotly_chart(fig_macd, use_container_width=True)
                else:
                    st.warning("No data")
            
            with tab4:
                st.subheader("Prediction Details")
                if components['predictor'].feature_names is not None:
                    feature_df = pd.DataFrame({
                        'Feature': components['predictor'].feature_names,
                        'Value': features.flatten()
                    })
                    st.dataframe(feature_df, use_container_width=True, hide_index=True)
                
                # FINAL UPDATED TEXT
st.markdown("**How it works:**")
st.info(
    "**Price-Based Rules:**\n"
    "- 📈 Price change > +1% → BUY (base score 0.7)\n"
    "- 📉 Price change < -0.5% → DON'T BUY (base score 0.3)\n"
    "- ⏸️ Price between -0.5% and +1% → HOLD (base score 0.5)\n\n"
    "**Minor adjustments (±0.05):**\n"
    "- Sentiment > 0.2 or RSI < 30 → +0.05\n"
    "- Sentiment < -0.2 or RSI > 70 → -0.05\n\n"
    "**Final Score > 0.6 = BUY**\n"
    "**Final Score < 0.4 = DON'T BUY**\n"
    "**Final Score between 0.4 and 0.6 = HOLD**"
)
if __name__ == "__main__":
    show_analysis()