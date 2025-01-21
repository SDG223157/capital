# app/utils/data/news_service.py

from sqlalchemy import create_engine, text, func, desc, case
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import os
from app.models import Base, NewsArticle, ArticleSymbol, ArticleMetric

class NewsService:
    def __init__(self):
        """Initialize database service with SQLAlchemy"""
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.engine = create_engine(
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:"
            f"{os.getenv('MYSQL_PASSWORD')}@"
            f"{os.getenv('MYSQL_HOST')}:"
            f"{os.getenv('MYSQL_PORT', '3306')}/"
            f"{os.getenv('MYSQL_DATABASE')}"
        )
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
    def initialize_tables(self):
        """Create database tables"""
        Base.metadata.create_all(self.engine)
        self.logger.info("Database tables initialized")

    def save_article(self, article_data: Dict) -> Optional[int]:
        """Save article using SQLAlchemy ORM"""
        session = self.Session()
        try:
            # Create NewsArticle instance
            article = NewsArticle(
                title=article_data['title'],
                content=article_data['content'],
                url=article_data['url'],
                published_at=datetime.strptime(article_data['published_at'], "%Y-%m-%d %H:%M:%S"),
                source=article_data['source'],
                sentiment_label=article_data['sentiment']['overall_sentiment'],
                sentiment_score=article_data['sentiment']['confidence'],
                brief_summary=article_data['summary']['brief'],
                key_points=article_data['summary']['key_points'],
                market_impact_summary=article_data['summary']['market_impact']
            )

            # Add symbols
            for symbol in article_data['symbols']:
                article.symbols.append(ArticleSymbol(symbol=symbol))

            # Add metrics
            if 'metrics' in article_data:
                # Add percentages
                for pct, context in zip(
                    article_data['metrics']['percentages'],
                    article_data['metrics']['percentage_contexts']
                ):
                    article.metrics.append(
                        ArticleMetric(
                            metric_type='percentage',
                            value=pct,
                            context=context
                        )
                    )

                # Add currencies
                for amount, context in zip(
                    article_data['metrics']['currencies'],
                    article_data['metrics']['currency_contexts']
                ):
                    try:
                        value = float(str(amount).replace(',', ''))
                        article.metrics.append(
                            ArticleMetric(
                                metric_type='currency',
                                value=value,
                                context=context
                            )
                        )
                    except ValueError:
                        self.logger.warning(f"Invalid currency value: {amount}")

            session.add(article)
            session.commit()
            return article.id

        except SQLAlchemyError as e:
            self.logger.error(f"Error saving article: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_articles_by_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        symbol: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """Get articles with pagination"""
        session = self.Session()
        try:
            query = session.query(NewsArticle)

            # Add date range filter
            query = query.filter(
                NewsArticle.published_at.between(
                    f"{start_date} 00:00:00",
                    f"{end_date} 23:59:59"
                )
            )

            # Add symbol filter if provided
            if symbol:
                query = query.join(ArticleSymbol).filter(ArticleSymbol.symbol == symbol)

            # Get total count for pagination
            total_count = query.count()

            # Add pagination
            query = query.order_by(desc(NewsArticle.published_at))
            query = query.offset((page - 1) * per_page).limit(per_page)

            # Execute query and convert to dict
            articles = [article.to_dict() for article in query.all()]
            
            return articles, total_count

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving articles: {e}")
            return [], 0
        finally:
            session.close()

    def get_sentiment_trends(
        self,
        symbol: str,
        days: int = 7
    ) -> List[Dict]:
        """Get sentiment trends over time"""
        session = self.Session()
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            results = (session.query(
                func.date(NewsArticle.published_at).label('date'),
                func.count().label('article_count'),
                func.avg(NewsArticle.sentiment_score).label('avg_sentiment'),
                func.sum(case([(NewsArticle.sentiment_label == 'POSITIVE', 1)], else_=0)).label('positive_count'),
                func.sum(case([(NewsArticle.sentiment_label == 'NEGATIVE', 1)], else_=0)).label('negative_count')
            )
            .join(ArticleSymbol)
            .filter(
                ArticleSymbol.symbol == symbol,
                NewsArticle.published_at >= start_date
            )
            .group_by(func.date(NewsArticle.published_at))
            .order_by(func.date(NewsArticle.published_at))
            .all())

            return [{
                'date': result.date.strftime('%Y-%m-%d'),
                'article_count': result.article_count,
                'avg_sentiment': float(result.avg_sentiment) if result.avg_sentiment else 0,
                'positive_count': result.positive_count,
                'negative_count': result.negative_count
            } for result in results]

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sentiment trends: {e}")
            return []
        finally:
            session.close()

    def get_related_symbols(self, symbol: str, min_occurrences: int = 2) -> List[Dict]:
        """Get symbols that frequently appear together"""
        session = self.Session()
        try:
            subquery = (session.query(NewsArticle.id)
                       .join(ArticleSymbol)
                       .filter(ArticleSymbol.symbol == symbol)
                       .subquery())

            results = (session.query(
                ArticleSymbol.symbol,
                func.count().label('occurrences')
            )
            .join(NewsArticle)
            .filter(
                NewsArticle.id.in_(subquery),
                ArticleSymbol.symbol != symbol
            )
            .group_by(ArticleSymbol.symbol)
            .having(func.count() >= min_occurrences)
            .order_by(desc('occurrences'))
            .all())

            return [{
                'symbol': result.symbol,
                'occurrences': result.occurrences
            } for result in results]

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving related symbols: {e}")
            return []
        finally:
            session.close()

    def search_articles(
        self,
        keyword: str,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """Search articles with various filters"""
        session = self.Session()
        try:
            query = session.query(NewsArticle)

            # Add keyword search
            query = query.filter(
                NewsArticle.content.like(f"%{keyword}%") |
                NewsArticle.title.like(f"%{keyword}%")
            )

            # Add symbol filter if provided
            if symbol:
                query = query.join(ArticleSymbol).filter(ArticleSymbol.symbol == symbol)

            # Add date range filter if provided
            if start_date:
                query = query.filter(NewsArticle.published_at >= f"{start_date} 00:00:00")
            if end_date:
                query = query.filter(NewsArticle.published_at <= f"{end_date} 23:59:59")

            # Get total count for pagination
            total_count = query.count()

            # Add pagination
            query = query.order_by(desc(NewsArticle.published_at))
            query = query.offset((page - 1) * per_page).limit(per_page)

            # Execute query and convert to dict
            articles = [article.to_dict() for article in query.all()]
            
            return articles, total_count

        except SQLAlchemyError as e:
            self.logger.error(f"Error searching articles: {e}")
            return [], 0
        finally:
            session.close()