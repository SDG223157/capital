# app/utils/news/news_service.py

from apify_client import ApifyClient
import logging
import os
from typing import List, Dict, Optional

class NewsService:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize NewsService with API token"""
        self.api_token = api_token or os.getenv('APIFY_TOKEN')
        if not self.api_token:
            raise ValueError("API token must be provided or set in APIFY_TOKEN environment variable")
        
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol: str) -> List[Dict]:
        """Get news for a symbol"""
        try:
            # Call the Apify actor
            run = self.client.actor("mscraper/tradingview-news-scraper").call(
                run_input={
                    "symbols": [symbol],
                    "proxy": {"useApifyProxy": True},
                    "resultsLimit": 100
                }
            )

            # Get dataset ID from the run result
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                self.logger.error("No dataset ID in response")
                return []

            # Get items from the dataset
            dataset = self.client.dataset(dataset_id)
            items = list(dataset.iterate_items())
            return items

        except Exception as e:
            self.logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []

if __name__ == "__main__":
    # Example usage
    service = NewsService()
    news = service.get_news("AAPL")
    print(f"Found {len(news)} articles")