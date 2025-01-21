# app/utils/news/news_service.py

from apify_client import ApifyClient
import logging
from typing import List, Dict, Optional
import os

class NewsService:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize NewsService with API token"""
        self.api_token = "apify_api_ewwcE7264pu0eRgeUBL2RaFk6rmCdy4AaAU9"
        if not self.api_token:
            raise ValueError("API token must be provided or set in APIFY_TOKEN environment variable")
        
        try:
            self.client = ApifyClient(self.api_token)
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            self.logger.error(f"Error initializing ApifyClient: {e}")
            raise

    def get_news(self, symbols: str) -> List[Dict]:
        """Get news articles for a specific symbol"""
        if not symbols:
            self.logger.error("Symbol cannot be empty")
            return []
            
        try:
            # Configure logging for debugging
            self.logger.debug(f"Getting news for symbols: {symbols}")
            self.logger.debug(f"Using API token: {self.api_token[:5]}...")

            # Get actor
            actor = self.client.actor("mscraper/tradingview-news-scraper")
            
            # Call actor
            self.logger.debug("Calling Apify actor")
            run = actor.call(
                run_input={
                    "symbols": symbols,
                    "proxy": {"useApifyProxy": True,"apifyProxyCountry": "US"},
                    "resultsLimit": 10
                }
            )

            # Get dataset ID
            dataset_id = run.get('defaultDatasetId')
            if not dataset_id:
                self.logger.error("No dataset ID in response")
                return []

            # Get items from dataset
            self.logger.debug(f"Getting items from dataset: {dataset_id}")
            dataset = self.client.dataset(dataset_id)
            items = list(dataset.iterate_items())
            self.logger.debug(f"Found {len(items)} items")
            
            return items

        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []

    @staticmethod
    def validate_api_token(api_token: str) -> bool:
        """Validate API token format"""
        if not api_token or len(api_token) < 10:
            return False
        return True