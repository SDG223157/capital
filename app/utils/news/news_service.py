# app/utils/news/news_service.py

from apify_client import ApifyClient
import logging
import os

class NewsService:
    def __init__(self, api_token=None):
        self.api_token = api_token or os.getenv('APIFY_TOKEN', 'test_token')
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol):
        try:
            run = self.client.actor("mscraper/tradingview-news-scraper").call(
                run_input={"symbols": [symbol]}
            )
            return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            return []