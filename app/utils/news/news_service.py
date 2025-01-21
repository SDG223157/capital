# app/utils/news/news_service.py

from apify_client import ApifyClient
import logging
from typing import List, Dict, Optional
import os

class NewsService:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize NewsService with API token"""
        self.api_token = api_token or os.getenv('APIFY_TOKEN')
        if not self.api_token:
            raise ValueError("API token must be provided or set in APIFY_TOKEN environment variable")
        
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol: str) -> List[Dict]:
        """Get news articles for a specific symbol"""
        if not symbol:
            self.logger.error("Symbol cannot be empty")
            return []
            
        try:
            # Get actor and run it
            actor = self.client.actor("mscraper/tradingview-news-scraper")
            run = actor.call(
                run_input={
                    "symbols": [symbol],
                    "proxy": {"useApifyProxy": True},
                    "resultsLimit": 100
                }
            )

            # Get dataset and items
            dataset_id = run.get('defaultDatasetId')
            if not dataset_id:
                self.logger.error("No dataset ID in response")
                return []

            dataset = self.client.dataset(dataset_id)
            return list(dataset.iterate_items())

        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []