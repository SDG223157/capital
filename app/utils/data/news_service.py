# app/data/news_service.py

from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import NewsArticle, ArticleSymbol, ArticleMetric

class NewsService:
    """Service class for handling news article operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'engine'):
                self.engine.dispose()
        except Exception as e:
            self.logger.error(f"Error disposing engine: {str(e)}")


    def save_article(self, article_data: Dict) -> Optional[int]:
        """
        Save article and related data to database
        
        Args:
            article_data (Dict): Dictionary containing article data including:
                - external_id: Unique identifier for the article
                - title: Article title
                - url: Article URL
                - published_at: Publication datetime
                - source: News source
                - sentiment: Dictionary with sentiment analysis results
                - summary: Dictionary with article summaries
                - symbols: List of stock symbols
                - metrics: Dictionary of article metrics
        
        Returns:
            Optional[int]: Article ID if successful, None if failed
        """
        try:
            external_id = article_data.get('external_id')
            if not external_id:
                self.logger.error("Article missing external ID")
                return None

            # Check for existing article
            existing_article = NewsArticle.query.filter_by(external_id=external_id).first()
            if existing_article:
                self.logger.debug(f"Article with external_id {external_id} already exists")
                return existing_article.id

            # Create new article
            article = NewsArticle(
                external_id=external_id,
                title=article_data.get('title'),
                url=article_data.get('url'),
                published_at=article_data.get('published_at'),
                source=article_data.get('source'),
                sentiment_label=article_data.get('sentiment', {}).get('overall_sentiment'),
                sentiment_score=article_data.get('sentiment', {}).get('confidence'),
                sentiment_explanation=article_data.get('sentiment', {}).get('explanation'),
                brief_summary=article_data.get('summary', {}).get('brief'),
                key_points=article_data.get('summary', {}).get('key_points'),
                market_impact_summary=article_data.get('summary', {}).get('market_impact')
            )

            # Process symbols
            if article_data.get('symbols'):
                self._add_symbols(article, article_data['symbols'])

            # Process metrics
            if article_data.get('metrics'):
                self._add_metrics(article, article_data['metrics'])

            # Save to database
            db.session.add(article)
            db.session.commit()
            
            self.logger.info(f"Successfully saved article with external_id: {external_id}")
            return article.id

        except SQLAlchemyError as e:
            self.logger.error(f"Database error while saving article: {str(e)}")
            db.session.rollback()
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error while saving article: {str(e)}")
            db.session.rollback()
            return None

    def _add_symbols(self, article: NewsArticle, symbols_data: List) -> None:
        """
        Add symbols to article
        
        Args:
            article (NewsArticle): Article object to add symbols to
            symbols_data (List): List of symbols or symbol dictionaries
        """
        for symbol_data in symbols_data:
            symbol = symbol_data.get('symbol') if isinstance(symbol_data, dict) else symbol_data
            if symbol:
                article.symbols.append(ArticleSymbol(symbol=symbol))

    def _add_metrics(self, article: NewsArticle, metrics_data: Dict) -> None:
        """
        Add metrics to article
        
        Args:
            article (NewsArticle): Article object to add metrics to
            metrics_data (Dict): Dictionary of metric data
        """
        for metric_type, metric_data in metrics_data.items():
            if isinstance(metric_data, dict):
                values = metric_data.get('values', [])
                contexts = metric_data.get('contexts', [])
                for value, context in zip(values, contexts):
                    article.metrics.append(
                        ArticleMetric(
                            metric_type=metric_type,
                            metric_value=value,
                            metric_context=context
                        )
                    )

    def get_articles_by_date_range(
        self,
        start_date: str,
        end_date: str,
        symbol: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        Get articles within date range with pagination
        
        Args:
            start_date (str): Start date in ISO format
            end_date (str): End date in ISO format
            symbol (str, optional): Filter by stock symbol
            page (int): Page number for pagination
            per_page (int): Number of items per page
            
        Returns:
            Tuple[List[Dict], int]: List of articles and total count
        """
        try:
            query = NewsArticle.query

            # Apply date range filter
            query = query.filter(
                NewsArticle.published_at.between(start_date, end_date)
            )

            # Apply symbol filter if provided
            if symbol:
                query = query.join(NewsArticle.symbols).filter(
                    ArticleSymbol.symbol == symbol
                )

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            paginated_articles = query.order_by(NewsArticle.published_at.desc())\
                                    .paginate(page=page, per_page=per_page, error_out=False)

            return [article.to_dict() for article in paginated_articles.items], total

        except Exception as e:
            self.logger.error(f"Error getting articles by date range: {str(e)}")
            return [], 0

    def search_articles(
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
        Search articles with various filters
        
        Args:
            keyword (str, optional): Search keyword for title and content
            symbol (str, optional): Filter by stock symbol
            start_date (str, optional): Start date in ISO format
            end_date (str, optional): End date in ISO format
            sentiment (str, optional): Filter by sentiment label
            page (int): Page number for pagination
            per_page (int): Number of items per page
            
        Returns:
            Tuple[List[Dict], int]: List of articles and total count
        """
        try:
            query = NewsArticle.query

            # Apply filters
            if keyword:
                query = query.filter(
                    db.or_(
                        NewsArticle.title.ilike(f'%{keyword}%'),
                        NewsArticle.brief_summary.ilike(f'%{keyword}%')
                    )
                )

            if symbol:
                query = query.join(NewsArticle.symbols).filter(
                    ArticleSymbol.symbol == symbol
                )

            if start_date:
                query = query.filter(NewsArticle.published_at >= start_date)

            if end_date:
                query = query.filter(NewsArticle.published_at <= end_date)

            if sentiment:
                query = query.filter(NewsArticle.sentiment_label == sentiment)

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            paginated_articles = query.order_by(NewsArticle.published_at.desc())\
                                    .paginate(page=page, per_page=per_page, error_out=False)

            return [article.to_dict() for article in paginated_articles.items], total

        except Exception as e:
            self.logger.error(f"Error searching articles: {str(e)}")
            return [], 0

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """
        Get article by ID
        
        Args:
            article_id (int): Article ID
            
        Returns:
            Optional[Dict]: Article data if found, None if not found
        """
        try:
            article = NewsArticle.query.get(article_id)
            return article.to_dict() if article else None
        except Exception as e:
            self.logger.error(f"Error getting article by ID: {str(e)}")
            return None

    def get_article_by_external_id(self, external_id: str) -> Optional[Dict]:
        """
        Get article by external ID
        
        Args:
            external_id (str): External article ID
            
        Returns:
            Optional[Dict]: Article data if found, None if not found
        """
        try:
            article = NewsArticle.query.filter_by(external_id=external_id).first()
            return article.to_dict() if article else None
        except Exception as e:
            self.logger.error(f"Error getting article by external ID: {str(e)}")
            return None

    def delete_article(self, article_id: int) -> bool:
        """
        Delete article by ID
        
        Args:
            article_id (int): Article ID
            
        Returns:
            bool: True if successful, False if failed
        """
        try:
            article = NewsArticle.query.get(article_id)
            if article:
                db.session.delete(article)
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting article: {str(e)}")
            db.session.rollback()
            return False