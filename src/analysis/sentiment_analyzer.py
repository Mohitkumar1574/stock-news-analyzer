import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import pandas as pd
from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

# Download required NLTK data
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
    def analyze_text(self, text):
        """
        Analyze sentiment of a single text using multiple methods
        """
        if not text or not isinstance(text, str):
            return {
                'vader_compound': 0,
                'vader_pos': 0,
                'vader_neu': 0,
                'vader_neg': 0,
                'textblob_polarity': 0,
                'textblob_subjectivity': 0,
                'sentiment_class': 'Neutral'
            }
        
        # VADER sentiment
        vader_scores = self.vader.polarity_scores(text)
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # Classify overall sentiment
        compound = vader_scores['compound']
        if compound >= 0.05:
            sentiment_class = 'Positive'
        elif compound <= -0.05:
            sentiment_class = 'Negative'
        else:
            sentiment_class = 'Neutral'
        
        return {
            'vader_compound': compound,
            'vader_pos': vader_scores['pos'],
            'vader_neu': vader_scores['neu'],
            'vader_neg': vader_scores['neg'],
            'textblob_polarity': textblob_polarity,
            'textblob_subjectivity': textblob_subjectivity,
            'sentiment_class': sentiment_class
        }
    
    def analyze_dataframe(self, df, text_column='title'):
        """
        Analyze sentiment for all rows in a dataframe
        """
        if df.empty or text_column not in df.columns:
            logger.warning("DataFrame empty or text column not found")
            return df
        
        sentiments = []
        for idx, row in df.iterrows():
            text = row[text_column]
            # Combine title and description if available
            if 'description' in df.columns and pd.notna(row['description']):
                text = text + " " + row['description']
            
            sentiment = self.analyze_text(text)
            sentiments.append(sentiment)
        
        sentiment_df = pd.DataFrame(sentiments)
        result = pd.concat([df, sentiment_df], axis=1)
        
        logger.info(f"Analyzed sentiment for {len(df)} articles")
        return result
    
    def get_average_sentiment(self, df):
        """Calculate average sentiment scores for the dataframe"""
        if df.empty or 'vader_compound' not in df.columns:
            return {'avg_compound': 0, 'avg_class': 'Neutral'}
        
        avg_compound = df['vader_compound'].mean()
        
        # Determine overall class
        if avg_compound >= 0.05:
            overall_class = 'Positive'
        elif avg_compound <= -0.05:
            overall_class = 'Negative'
        else:
            overall_class = 'Neutral'
        
        return {
            'avg_compound': avg_compound,
            'avg_class': overall_class,
            'positive_pct': (df['sentiment_class'] == 'Positive').mean() * 100,
            'negative_pct': (df['sentiment_class'] == 'Negative').mean() * 100,
            'neutral_pct': (df['sentiment_class'] == 'Neutral').mean() * 100
        }