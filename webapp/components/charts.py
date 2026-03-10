import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_candlestick_chart(df, title="Stock Price"):
    """Create candlestick chart from dataframe"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    )])
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Price")
    return fig

def create_sentiment_pie(sentiment_summary):
    """Create pie chart for sentiment distribution"""
    fig = go.Figure(data=[go.Pie(
        labels=['Positive', 'Negative', 'Neutral'],
        values=[sentiment_summary['positive_pct'], 
                sentiment_summary['negative_pct'], 
                sentiment_summary['neutral_pct']],
        hole=.3
    )])
    fig.update_layout(title="Sentiment Distribution")
    return fig