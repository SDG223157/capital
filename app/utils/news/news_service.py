# app/utils/news/news_service.py

from apify_client import ApifyClient
import logging
import os
from typing import List, Dict, Optional

class NewsService:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize the NewsService
        
        Args:
            api_token: Optional API token. If not provided, uses APIFY_TOKEN env var.
        """
        self.api_token = api_token or os.getenv('APIFY_TOKEN')
        if not self.api_token:
            raise ValueError("API token must be provided or set in APIFY_TOKEN environment variable")
            
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol: str) -> List[Dict]:
        """Get news for a specific symbol
        
        Args:
            symbol: Stock symbol to get news for
            
        Returns:
            List of news articles
        """
        try:
            # Set up the actor input
            run_input = {
                "symbols": [symbol],
                "proxy": {"useApifyProxy": True},
                "resultsLimit": 100
            }
            
            # Run the actor
            self.logger.debug(f"Running actor for symbol: {symbol}")
            run = self.client.actor("mscraper/tradingview-news-scraper").call(
                run_input=run_input
            )
            
            # Get the dataset ID
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                self.logger.error("No dataset ID returned from actor")
                return []
                
            # Get the items from the dataset
            self.logger.debug(f"Fetching items from dataset: {dataset_id}")
            return list(self.client.dataset(dataset_id).iterate_items())
            
        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []