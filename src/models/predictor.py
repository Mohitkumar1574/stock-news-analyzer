import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

class StockPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = None
        
    def prepare_features(self, news_df, stock_data):
        """
        Prepare feature vector from news sentiment and stock data
        Returns a single feature vector for current state
        """
        features = []
        
        # Average sentiment from recent news
        if not news_df.empty and 'vader_compound' in news_df.columns:
            avg_sentiment = news_df['vader_compound'].mean()
            sentiment_std = news_df['vader_compound'].std()
            positive_ratio = (news_df['sentiment_class'] == 'Positive').mean()
            negative_ratio = (news_df['sentiment_class'] == 'Negative').mean()
        else:
            avg_sentiment = 0
            sentiment_std = 0
            positive_ratio = 0
            negative_ratio = 0
        
        # Stock features
        current_price = stock_data.get('current_price', 0)
        day_change = stock_data.get('day_change', 0)
        volume = stock_data.get('volume', 0) / 1e6  # in millions
        pe_ratio = stock_data.get('pe_ratio', 15) if stock_data.get('pe_ratio') else 15
        
        # Technical indicators from historical data (if available)
        hist = stock_data.get('historical', pd.DataFrame())
        if not hist.empty and 'Close' in hist.columns:
            latest_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else latest_close
            short_term_trend = (latest_close - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5] if len(hist) >= 5 else 0
            volatility = hist['Close'].pct_change().std() * np.sqrt(252)  # annualized
        else:
            short_term_trend = 0
            volatility = 0.3  # default
        
        feature_vector = [
            avg_sentiment,
            sentiment_std,
            positive_ratio,
            negative_ratio,
            day_change,
            volume,
            pe_ratio,
            short_term_trend,
            volatility
        ]
        
        self.feature_names = [
            'avg_sentiment', 'sentiment_std', 'positive_ratio', 'negative_ratio',
            'day_change', 'volume_millions', 'pe_ratio', 'short_term_trend', 'volatility'
        ]
        
        return np.array(feature_vector).reshape(1, -1)
    
    def prepare_training_data(self, historical_data_list):
        """
        Prepare training data from historical records
        historical_data_list: list of dicts with 'news_df', 'stock_data', and 'next_day_return' (label)
        """
        X = []
        y = []
        
        for record in historical_data_list:
            features = self.prepare_features(record['news_df'], record['stock_data'])
            X.append(features.flatten())
            
            # Label: 1 if next day return > 1%, else 0
            label = 1 if record.get('next_day_return', 0) > 0.01 else 0
            y.append(label)
        
        return np.array(X), np.array(y)
    
    def train(self, X, y):
        """Train Random Forest model"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Model training completed. Accuracy: {accuracy:.4f}")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        return accuracy
    
    def predict(self, features):
        """Predict buy/don't buy for current features"""
        if self.model is None:
            logger.error("Model not trained. Please train first.")
            return None, None
        
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        
        return prediction, probabilities
    
    def save_model(self, filepath):
        """Save trained model to disk"""
        if self.model:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            joblib.dump(self.model, filepath)
            logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model from disk"""
        if os.path.exists(filepath):
            self.model = joblib.load(filepath)
            logger.info(f"Model loaded from {filepath}")
        else:
            logger.error(f"Model file not found: {filepath}")