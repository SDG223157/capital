# app/utils/analysis/news_service.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from ..config.news_config import NewsConfig
from .news_analyzer import NewsAnalyzer
from ..data.news_service import NewsService
from apify_client import ApifyClient

class NewsAnalysisService:
    def __init__(self):
        """Initialize the news analysis service"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.analyzer = NewsAnalyzer("apify_api_ewwcE7264pu0eRgeUBL2RaFk6rmCdy4AaAU9")
        self.db = NewsService()
        
        # Initialize database
        self.db.initialize_tables()
        
    def fetch_and_analyze_news(self, symbols: List[str], limit: int = NewsConfig.MAX_ARTICLES) -> List[Dict]:
        """
        Fetch news articles from Apify, analyze them, and store in database
        
        Args:
            symbols (List[str]): List of stock symbols to fetch news for
            limit (int): Maximum number of articles to fetch
            
        Returns:
            List[Dict]: List of analyzed news articles
        """
        try:
            # 1. Fetch raw news from Apify
            self.logger.info(f"Fetching news for symbols: {symbols}")
            raw_articles = self.analyzer.get_news(symbols, limit)
            
            if not raw_articles:
                self.logger.warning(f"No articles found for symbols: {symbols}")
                return []
                
            self.logger.info(f"Fetched {len(raw_articles)} articles")
            
            # 2. Process and analyze each article
            analyzed_articles = []
            for article in raw_articles:
                try:
                    # Analyze the article
                    analyzed = self.analyzer.analyze_article(article)
                    if analyzed:
                        # Save to database
                        article_id = self.db.save_article(analyzed)
                        if article_id:
                            analyzed['id'] = article_id
                            analyzed_articles.append(analyzed)
                        else:
                            self.logger.error(f"Failed to save article: {article.get('title', 'Unknown')}")
                except Exception as e:
                    self.logger.error(f"Error processing article: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully processed {len(analyzed_articles)} articles")
            return analyzed_articles
            
        except Exception as e:
            self.logger.error(f"Error in fetch_and_analyze_news: {str(e)}")
            return []

    def get_news_by_date_range(
        self,
        start_date: str,
        end_date: str,
        symbol: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        Get news articles within a date range
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            symbol (str, optional): Filter by symbol
            page (int): Page number for pagination
            per_page (int): Items per page
            
        Returns:
            Tuple[List[Dict], int]: List of articles and total count
        """
        try:
            return self.db.get_articles_by_date_range(
                start_date=start_date,
                end_date=end_date,
                symbol=symbol,
                page=page,
                per_page=per_page
            )
        except Exception as e:
            self.logger.error(f"Error getting articles by date range: {str(e)}")
            return [], 0

    def get_sentiment_summary(
        self,
        date: str = None,
        symbol: str = None,
        days: int = 7
    ) -> Dict:
        """
        Get sentiment summary statistics
        
        Args:
            date (str, optional): Specific date for summary
            symbol (str, optional): Filter by symbol
            days (int): Number of days to analyze if no specific date
            
        Returns:
            Dict: Sentiment summary statistics
        """
        try:
            if date:
                return self.db.get_daily_sentiment_summary(date, symbol)
            else:
                # Calculate summary for last N days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                articles, _ = self.db.get_articles_by_date_range(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    symbol=symbol
                )
                
                if not articles:
                    return {
                        "total_articles": 0,
                        "sentiment_distribution": {
                            "positive": 0,
                            "negative": 0,
                            "neutral": 0
                        },
                        "average_sentiment": 0
                    }
                
                # Calculate statistics
                positive = sum(1 for a in articles if a['sentiment_label'] == 'POSITIVE')
                negative = sum(1 for a in articles if a['sentiment_label'] == 'NEGATIVE')
                neutral = sum(1 for a in articles if a['sentiment_label'] == 'NEUTRAL')
                
                return {
                    "total_articles": len(articles),
                    "sentiment_distribution": {
                        "positive": positive,
                        "negative": negative,
                        "neutral": neutral
                    },
                    "average_sentiment": sum(a['sentiment_score'] for a in articles) / len(articles)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting sentiment summary: {str(e)}")
            return {}

    def get_trending_topics(self, days: int = NewsConfig.TRENDING_DAYS) -> List[Dict]:
        """
        Get trending topics from recent news
        
        Args:
            days (int): Number of days to analyze
            
        Returns:
            List[Dict]: Trending topics with statistics
        """
        try:
            return self.db.get_trending_topics(days)
        except Exception as e:
            self.logger.error(f"Error getting trending topics: {str(e)}")
            return []

    def search_news(
        self,
        keyword: str = None,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None,
        sentiment: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        Search news articles with various filters
        
        Args:
            keyword (str, optional): Search keyword
            symbol (str, optional): Filter by symbol
            start_date (str, optional): Start date filter
            end_date (str, optional): End date filter
            sentiment (str, optional): Filter by sentiment
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            Tuple[List[Dict], int]: List of articles and total count
        """
        try:
            return self.db.search_articles(
                keyword=keyword,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                sentiment=sentiment,
                page=page,
                per_page=per_page
            )
        except Exception as e:
            self.logger.error(f"Error searching articles: {str(e)}")
            return [], 0

    def close(self):
        """Clean up resources"""
        try:
            self.db.close()
        except Exception as e:
            self.logger.error(f"Error closing database connection: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize service
    service = NewsAnalysisService()
    
    try:
        # Fetch and analyze news
        articles = service.fetch_and_analyze_news(
            symbols=["NASDAQ:GOOGL", "NYSE:AAPL"],
            limit=10
        )
        
        # Get sentiment summary
        summary = service.get_sentiment_summary(
            symbol="NASDAQ:GOOGL",
            days=7
        )
        
        # Search articles
        results, total = service.search_news(
            keyword="earnings",
            symbol="NASDAQ:GOOGL",
            page=1,
            per_page=20
        )
        
        print(f"Fetched {len(articles)} articles")
        print(f"Sentiment summary: {summary}")
        print(f"Search results: {total} total matches")
        
    finally:
        service.close()