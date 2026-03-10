import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/stock_news.db')
    MODEL_PATH = os.getenv('MODEL_PATH', './data/models/')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

config = Config()