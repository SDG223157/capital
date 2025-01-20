# app/utils/news/news_service.py

from apify_client import ApifyClient
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import os

class NewsService:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize NewsService
        
        Args:
            api_token (str, optional): Apify API token. If not provided, 
                                     will try to get from environment variable.
        """
        self.api_token = api_token or os.getenv('APIFY_TOKEN')
        if not self.api_token:
            raise ValueError("API token must be provided or set in APIFY_TOKEN environment variable")
            
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol: str, days: int = 7) -> List[Dict]:
        """Fetch news for a symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            days (int): Number of days of news to fetch
            
        Returns:
            List[Dict]: List of news articles
        """
        try:
            run_input = {
                "symbols": [symbol],
                "proxy": {"useApifyProxy": True},
                "resultsLimit": 100
            }
            
            self.logger.info(f"Fetching news for {symbol}")
            run = self.client.actor("mscraper/tradingview-news-scraper").call(
                run_input=run_input
            )
            
            dataset_id = run["defaultDatasetId"]
            articles = list(self.client.dataset(dataset_id).iterate_items())
            self.logger.info(f"Found {len(articles)} articles for {symbol}")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return []