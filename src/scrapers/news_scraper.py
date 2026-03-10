import requests
import pandas as pd
from datetime import datetime, timedelta
from src.utils.config import config
from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

class NewsScraper:
    def __init__(self):
        self.api_key = config.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2/everything"
        
    def fetch_company_news(self, company_name, days=7):
        """
        Fetch news articles about a company from NewsAPI
        """
        if not self.api_key or self.api_key == 'your_api_key_here':
            logger.error("NewsAPI key not set. Please add your API key to .env file.")
            return pd.DataFrame()
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'q': company_name,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'sortBy': 'publishedAt',
            'language': 'en',
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                news_list = []
                for article in articles:
                    news_list.append({
                        'title': article['title'],
                        'description': article['description'],
                        'content': article['content'],
                        'published_at': article['publishedAt'],
                        'source': article['source']['name'],
                        'url': article['url']
                    })
                
                df = pd.DataFrame(news_list)
                logger.info(f"Fetched {len(df)} news articles for {company_name}")
                return df
            else:
                logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return pd.DataFrame()
    
    def fetch_multiple_companies(self, companies, days=7):
        """Fetch news for multiple companies"""
        all_news = []
        for company in companies:
            df = self.fetch_company_news(company, days)
            if not df.empty:
                df['company'] = company
                all_news.append(df)
        
        if all_news:
            return pd.concat(all_news, ignore_index=True)
        return pd.DataFrame()