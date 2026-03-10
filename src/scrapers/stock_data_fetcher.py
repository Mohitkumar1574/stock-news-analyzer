import yfinance as yf
import pandas as pd
import numpy as np
from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.cache = {}
        
    def get_stock_data(self, symbol, period='1mo', interval='1d'):
        """
        Fetch stock data from Yahoo Finance
        """
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                logger.warning(f"No data found for symbol: {symbol}")
                return None
            
            # Get current info
            info = stock.info
            
            stock_data = {
                'historical': hist,
                'current_price': info.get('regularMarketPrice', hist['Close'].iloc[-1]),
                'previous_close': info.get('regularMarketPreviousClose', hist['Close'].iloc[-2] if len(hist) > 1 else None),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', hist['Volume'].iloc[-1] if 'Volume' in hist else 0),
                'pe_ratio': info.get('trailingPE', None),
                'day_high': info.get('dayHigh', hist['High'].iloc[-1] if 'High' in hist else None),
                'day_low': info.get('dayLow', hist['Low'].iloc[-1] if 'Low' in hist else None),
                'symbol': symbol,
                'name': info.get('longName', symbol)
            }
            
            # Calculate daily change
            if stock_data['previous_close']:
                stock_data['day_change'] = ((stock_data['current_price'] - stock_data['previous_close']) / stock_data['previous_close']) * 100
            else:
                stock_data['day_change'] = 0
                
            logger.info(f"Fetched stock data for {symbol}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, start_date, end_date):
        """Fetch historical data for a date range"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)
            return hist
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def get_multiple_stocks(self, symbols):
        """Fetch data for multiple stocks"""
        results = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data:
                results[symbol] = data
        return results