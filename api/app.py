from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.news_scraper import NewsScraper
from src.scrapers.stock_data_fetcher import StockDataFetcher
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.models.predictor import StockPredictor

app = FastAPI(title="Stock News Analyzer API")

# Initialize components
news_scraper = NewsScraper()
stock_fetcher = StockDataFetcher()
sentiment_analyzer = SentimentAnalyzer()
predictor = StockPredictor()

class AnalyzeRequest(BaseModel):
    company: str
    symbol: str
    days: int = 7

@app.get("/")
def root():
    return {"message": "Stock News Analyzer API"}

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    # Fetch news
    news_df = news_scraper.fetch_company_news(request.company, request.days)
    if news_df.empty:
        raise HTTPException(status_code=404, detail="No news found")
    
    # Sentiment analysis
    news_df = sentiment_analyzer.analyze_dataframe(news_df)
    sentiment_summary = sentiment_analyzer.get_average_sentiment(news_df)
    
    # Fetch stock data
    stock_data = stock_fetcher.get_stock_data(request.symbol, period=f"{max(request.days, 30)}d")
    if not stock_data:
        raise HTTPException(status_code=404, detail="Stock data not found")
    
    # Prepare features and make prediction
    features = predictor.prepare_features(news_df, stock_data)
    
    # Simple heuristic (replace with actual model)
    buy_score = 0.5 + sentiment_summary['avg_compound'] * 0.3
    buy_score = max(0, min(1, buy_score))
    
    return {
        "company": request.company,
        "symbol": request.symbol,
        "current_price": stock_data['current_price'],
        "day_change": stock_data['day_change'],
        "sentiment": sentiment_summary,
        "recommendation": "BUY" if buy_score > 0.6 else "DON'T BUY" if buy_score < 0.4 else "HOLD",
        "confidence": buy_score * 100,
        "news_count": len(news_df)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)