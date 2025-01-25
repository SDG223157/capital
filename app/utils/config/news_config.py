# app/utils/config/news_config.py
import os
class NewsConfig:
    # Database configuration
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'your_username',
        'password': 'your_password',
        'database': 'news_analysis'
    }
    
    # API configuration
    APIFY_TOKEN = os.getenv('APIFY_TOKEN')
    
    # Analysis configuration
    MAX_ARTICLES = 50
    DEFAULT_SUMMARY_LENGTH = 3
    MIN_WORD_LENGTH = 3
    
    # Trending topics configuration
    TRENDING_DAYS = 7
    MIN_TOPIC_MENTIONS = 2
    
    # Excluded words for topic analysis
    EXCLUDED_WORDS = {
        'this', 'that', 'with', 'from', 'what', 'where', 'when',
        'have', 'your', 'will', 'about', 'they', 'their'
    }
    
    # Market-related terms for impact analysis
    MARKET_TERMS = {
        'revenue', 'profit', 'earnings', 'growth', 'decline', 
        'market', 'stock', 'shares', 'price', 'trading',
        'valuation', 'forecast', 'guidance', 'outlook'
    }
    DEFAULT_SYMBOLS = [
    "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL", "NASDAQ:META",
    "NASDAQ:NVDA", "NASDAQ:TSLA", "NYSE:BRK.A", "NYSE:V", "NYSE:JPM",
    "NYSE:JNJ", "NYSE:WMT", "NYSE:MA", "NYSE:PG", "NASDAQ:AVGO",
    "NYSE:CVX", "NYSE:HD", "NYSE:MRK", "NYSE:KO", "NASDAQ:PEP", 
    "NYSE:BAC", "NYSE:DIS", "NASDAQ:COST", "NASDAQ:CSCO", "NYSE:VZ",
    "NYSE:ABT", "NASDAQ:ADBE", "NASDAQ:CMCSA", "NYSE:NKE", "NYSE:TMO"
    ]