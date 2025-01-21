# app/utils/news/news_service.py

from apify_client import ApifyClient
import logging
from typing import List, Dict, Optional
import os

class NewsService:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv('APIFY_TOKEN')
        if not self.api_token:
            raise ValueError("API token must be provided or set in APIFY_TOKEN environment variable")
        
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol: str) -> List[Dict]:
        try:
            # Get the actor instance
            actor = self.client.actor("mscraper/tradingview-news-scraper")
            
            # Run the actor
            run = actor.call(
                run_input={
                    "symbols": [symbol],
                    "proxy": {"useApifyProxy": True},
                    "resultsLimit": 100
                }
            )

            if not run or 'defaultDatasetId' not in run:
                self.logger.error("Invalid response from Apify actor")
                return []

            # Get the dataset items
            dataset = self.client.dataset(run['defaultDatasetId'])
            return list(dataset.iterate_items())

        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []