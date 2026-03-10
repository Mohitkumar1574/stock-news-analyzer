import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD and signal line"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        return upper_band, rolling_mean, lower_band
    
    @staticmethod
    def calculate_moving_averages(prices):
        """Calculate various moving averages"""
        ma20 = prices.rolling(window=20).mean()
        ma50 = prices.rolling(window=50).mean()
        ma200 = prices.rolling(window=200).mean()
        return ma20, ma50, ma200
    
    @staticmethod
    def add_all_indicators(df, price_col='Close'):
        """Add all technical indicators to dataframe"""
        prices = df[price_col]
        
        df['RSI'] = TechnicalIndicators.calculate_rsi(prices)
        df['MACD'], df['Signal'], df['MACD_Hist'] = TechnicalIndicators.calculate_macd(prices)
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = TechnicalIndicators.calculate_bollinger_bands(prices)
        df['MA20'], df['MA50'], df['MA200'] = TechnicalIndicators.calculate_moving_averages(prices)
        
        # Price position relative to moving averages
        df['Above_MA20'] = (df[price_col] > df['MA20']).astype(int)
        df['Above_MA50'] = (df[price_col] > df['MA50']).astype(int)
        
        return df