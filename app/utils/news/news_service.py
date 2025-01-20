# app/utils/news/news_service.py
from apify_client import ApifyClient
from datetime import datetime, timedelta
import logging

from app.utils.config.analyze_config import AnalyzeConfig

class NewsService:
    def __init__(self):
        self.client = ApifyClient(AnalyzeConfig.APIFY_TOKEN)
        self.logger = logging.getLogger(__name__)

    def get_news(self, symbol: str, days: int = 7):
        """Fetch news from TradingView"""
        try:
            run_input = {
                "symbols": [symbol],
                "proxy": {"useApifyProxy": True},
                "resultsLimit": 100
            }
            
            run = self.client.actor("mscraper/tradingview-news-scraper").call(
                run_input=run_input
            )
            
            return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            return []