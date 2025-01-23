# app/utils/analysis/news_service.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import traceback
from app.utils.data.news_service import NewsService
from .news_analyzer import NewsAnalyzer

class NewsAnalysisService:
    def __init__(self):
        """Initialize the news analysis service"""
        self.logger = logging.getLogger(__name__)
        self.analyzer = NewsAnalyzer("apify_api_ewwcE7264pu0eRgeUBL2RaFk6rmCdy4AaAU9")
        self.db = NewsService()

    def search_articles(self, keyword=None, symbol=None, start_date=None, 
                       end_date=None, sentiment=None, page=1, per_page=20):
        """
        Search articles (renamed from search_news to match route expectations)
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
            if hasattr(self.db, 'engine'):
                self.db.engine.dispose()
        except Exception as e:
            self.logger.error(f"Error closing resources: {str(e)}")
        
    def fetch_and_analyze_news(self, symbols: List[str], limit: int = 10) -> List[Dict]:
        """
        Fetch news articles from Apify, analyze them, and store in database
        """
        try:
            self.logger.info(f"Starting news fetch for symbols: {symbols}")
            
            if not symbols or not isinstance(symbols, list) or not isinstance(limit, int) or limit <= 0:
                self.logger.error(f"Invalid input parameters: symbols={symbols}, limit={limit}")
                return []

            # 1. Fetch raw news
            raw_articles = self.analyzer.get_news(symbols, limit)
            if not raw_articles:
                return []
            
            # 2. Process and analyze articles
            analyzed_articles = []
            for idx, article in enumerate(raw_articles, 1):
                try:
                    if not article:
                        continue
                        
                    # Analyze article
                    analyzed = self.analyzer.analyze_article(article)
                    if not analyzed or not self._validate_article(analyzed):
                        continue
                    
                    # Save to database
                    article_id = self.db.save_article(analyzed)
                    if article_id:
                        analyzed['id'] = article_id
                        analyzed_articles.append(analyzed)
                    
                except Exception as e:
                    self.logger.error(f"Error processing article {idx}: {str(e)}")
                    continue
            
            return analyzed_articles
            
        except Exception as e:
            self.logger.error(f"Error in fetch_and_analyze_news: {str(e)}")
            return []

    def _validate_article(self, article: Dict) -> bool:
        """Validate required article fields"""
        required_fields = ['external_id', 'title', 'published_at']
        return all(article.get(field) for field in required_fields)

    def get_news_by_date_range(
        self,
        start_date: str,
        end_date: str,
        symbol: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """Get news articles within a date range"""
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
        """Search news articles with various filters"""
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

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """Get article by ID"""
        try:
            return self.db.get_article_by_id(article_id)
        except Exception as e:
            self.logger.error(f"Error getting article by ID: {str(e)}")
            return None

    def get_article_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Get article by external ID"""
        try:
            return self.db.get_article_by_external_id(external_id)
        except Exception as e:
            self.logger.error(f"Error getting article by external ID: {str(e)}")
            return None

    def close(self):
        """Clean up resources"""
        try:
            self.db.close()
        except Exception as e:
            self.logger.error(f"Error closing resources: {str(e)}")