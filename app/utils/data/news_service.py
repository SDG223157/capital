# app/utils/data/news_service.py

from typing import Dict, List, Tuple
import logging
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
import os

class NewsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize database connection using SQLAlchemy
        self.engine = create_engine(
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:"
            f"{os.getenv('MYSQL_PASSWORD')}@"
            f"{os.getenv('MYSQL_HOST')}:"
            f"{os.getenv('MYSQL_PORT', '3306')}/"
            f"{os.getenv('MYSQL_DATABASE')}"
        )

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False

    def initialize_tables(self):
        """Create necessary database tables if they don't exist"""
        try:
            with self.engine.connect() as conn:
                # Create news articles table
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS news_articles (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        content TEXT,
                        url VARCHAR(512),
                        published_at DATETIME,
                        source VARCHAR(100),
                        sentiment_label VARCHAR(20),
                        sentiment_score FLOAT,
                        sentiment_explanation TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        brief_summary TEXT,
                        key_points TEXT,
                        market_impact TEXT
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                '''))

                # Create article symbols table
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS article_symbols (
                        article_id INT,
                        symbol VARCHAR(20),
                        FOREIGN KEY (article_id) REFERENCES news_articles(id) ON DELETE CASCADE,
                        PRIMARY KEY (article_id, symbol)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                '''))

                # Create article metrics table
                conn.execute(text('''
                    CREATE TABLE IF NOT EXISTS article_metrics (
                        article_id INT,
                        metric_type VARCHAR(50),
                        metric_value FLOAT,
                        metric_context TEXT,
                        FOREIGN KEY (article_id) REFERENCES news_articles(id) ON DELETE CASCADE,
                        PRIMARY KEY (article_id, metric_type)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                '''))

                conn.commit()
                self.logger.info("Database tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing tables: {str(e)}")
            raise

    def save_article(self, article: Dict) -> int:
        """Save article and related data to database"""
        try:
            with self.engine.connect() as conn:
                # Check if article already exists by external_id
                external_id = article.get('id')
                if not external_id:
                    self.logger.error("Article missing external ID")
                    return None

                # Begin transaction
                with conn.begin():
                    # Check for existing article
                    result = conn.execute(
                        text("SELECT id FROM news_articles WHERE external_id = :external_id"),
                        {"external_id": external_id}
                    )
                    existing_article = result.fetchone()

                    if existing_article:
                        self.logger.debug(f"Article with external_id {external_id} already exists")
                        return existing_article[0]

                    # Insert new article
                    result = conn.execute(text('''
                        INSERT INTO news_articles (
                            external_id, title, content, url, published_at, source,
                            sentiment_label, sentiment_score, sentiment_explanation,
                            brief_summary, key_points, market_impact_summary
                        ) VALUES (
                            :external_id, :title, :content, :url, :published_at, :source,
                            :sentiment_label, :sentiment_score, :sentiment_explanation,
                            :brief_summary, :key_points, :market_impact_summary
                        )
                        RETURNING id
                    '''), {
                        'external_id': external_id,
                        'title': article.get('title'),
                        'content': article.get('content'),
                        'url': article.get('url'),
                        'published_at': article.get('published_at'),
                        'source': article.get('source'),
                        'sentiment_label': article.get('sentiment', {}).get('overall_sentiment'),
                        'sentiment_score': article.get('sentiment', {}).get('confidence'),
                        'sentiment_explanation': article.get('sentiment', {}).get('explanation'),
                        'brief_summary': article.get('summary', {}).get('brief'),
                        'key_points': article.get('summary', {}).get('key_points'),
                        'market_impact_summary': article.get('summary', {}).get('market_impact')
                    })
                    
                    article_id = result.fetchone()[0]

                    # Insert symbols - Handle both dictionary and string formats
                    if article.get('symbols'):
                        symbol_values = []
                        for symbol_data in article['symbols']:
                            # Handle both formats: {'symbol': 'NASDAQ:TSLA'} and 'NASDAQ:TSLA'
                            symbol = symbol_data.get('symbol') if isinstance(symbol_data, dict) else symbol_data
                            if symbol:
                                symbol_values.append({'article_id': article_id, 'symbol': symbol})
                        
                        if symbol_values:
                            conn.execute(text('''
                                INSERT INTO article_symbols (article_id, symbol)
                                VALUES (:article_id, :symbol)
                                ON CONFLICT (article_id, symbol) DO NOTHING
                            '''), symbol_values)

                    # Insert metrics
                    if article.get('metrics'):
                        for metric_type, metric_data in article['metrics'].items():
                            if isinstance(metric_data, dict):
                                values = metric_data.get('values', [])
                                contexts = metric_data.get('contexts', [])
                                for value, context in zip(values, contexts):
                                    conn.execute(text('''
                                        INSERT INTO article_metrics 
                                        (article_id, metric_type, value, context)
                                        VALUES (:article_id, :metric_type, :value, :context)
                                    '''), {
                                        'article_id': article_id,
                                        'metric_type': metric_type,
                                        'value': value,
                                        'context': context
                                    })

                    return article_id

        except Exception as e:
            self.logger.error(f"Error saving article: {str(e)}", exc_info=True)
            return None

    def get_articles_by_date_range(
        self,
        start_date: str,
        end_date: str,
        symbol: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Dict], int]:
        """Get articles within date range with pagination"""
        try:
            with self.engine.connect() as conn:
                # Build base query
                query = '''
                    SELECT DISTINCT 
                        na.*, 
                        GROUP_CONCAT(DISTINCT as_.symbol) as symbols,
                        GROUP_CONCAT(DISTINCT CONCAT(am.metric_type, ':', am.metric_value, '|', am.metric_context)) as metrics
                    FROM news_articles na
                    LEFT JOIN article_symbols as_ ON na.id = as_.article_id
                    LEFT JOIN article_metrics am ON na.id = am.article_id
                    WHERE na.published_at BETWEEN :start_date AND :end_date
                '''
                params = {'start_date': start_date, 'end_date': end_date}

                if symbol:
                    query += ' AND as_.symbol = :symbol'
                    params['symbol'] = symbol

                # Get total count
                count_query = query.replace(
                    'SELECT DISTINCT \n                        na.*', 
                    'SELECT COUNT(DISTINCT na.id) as count'
                )
                count_query = count_query.split('GROUP BY')[0]
                
                result = conn.execute(text(count_query), params)
                total = result.fetchone()[0]

                # Add grouping and pagination
                query += ' GROUP BY na.id ORDER BY na.published_at DESC LIMIT :limit OFFSET :offset'
                params['limit'] = per_page
                params['offset'] = (page - 1) * per_page

                # Execute main query
                result = conn.execute(text(query), params)
                articles = []
                
                for row in result:
                    article = dict(row)
                    # Process symbols
                    article['symbols'] = (
                        article['symbols'].split(',') 
                        if article['symbols'] else []
                    )
                    
                    # Process metrics
                    metrics = {}
                    if article['metrics']:
                        for metric_str in article['metrics'].split(','):
                            try:
                                metric_type, data = metric_str.split(':')
                                value, context = data.split('|')
                                if metric_type not in metrics:
                                    metrics[metric_type] = {
                                        'values': [], 'contexts': []
                                    }
                                metrics[metric_type]['values'].append(float(value))
                                metrics[metric_type]['contexts'].append(context)
                            except:
                                continue
                    article['metrics'] = metrics
                    
                    articles.append(article)

                return articles, total

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
        """Search articles with various filters"""
        try:
            with self.engine.connect() as conn:
                query = '''
                    SELECT DISTINCT 
                        na.*, 
                        GROUP_CONCAT(DISTINCT as_.symbol) as symbols,
                        GROUP_CONCAT(DISTINCT CONCAT(am.metric_type, ':', am.metric_value, '|', am.metric_context)) as metrics
                    FROM news_articles na
                    LEFT JOIN article_symbols as_ ON na.id = as_.article_id
                    LEFT JOIN article_metrics am ON na.id = am.article_id
                    WHERE 1=1
                '''
                params = {}

                if keyword:
                    query += ' AND (na.title LIKE :keyword OR na.content LIKE :keyword)'
                    params['keyword'] = f'%{keyword}%'

                if symbol:
                    query += ' AND as_.symbol = :symbol'
                    params['symbol'] = symbol

                if start_date:
                    query += ' AND na.published_at >= :start_date'
                    params['start_date'] = start_date

                if end_date:
                    query += ' AND na.published_at <= :end_date'
                    params['end_date'] = end_date

                if sentiment:
                    query += ' AND na.sentiment_label = :sentiment'
                    params['sentiment'] = sentiment

                # Get total count
                count_query = query.replace(
                    'SELECT DISTINCT \n                        na.*', 
                    'SELECT COUNT(DISTINCT na.id) as count'
                )
                count_query = count_query.split('GROUP BY')[0]
                
                result = conn.execute(text(count_query), params)
                total = result.fetchone()[0]

                # Add grouping and pagination
                query += ''' 
                    GROUP BY na.id 
                    ORDER BY na.published_at DESC 
                    LIMIT :limit OFFSET :offset
                '''
                params['limit'] = per_page
                params['offset'] = (page - 1) * per_page

                # Execute main query
                result = conn.execute(text(query), params)
                articles = []
                
                for row in result:
                    article = dict(row)
                    # Process symbols
                    article['symbols'] = (
                        article['symbols'].split(',') 
                        if article['symbols'] else []
                    )
                    
                    # Process metrics
                    metrics = {}
                    if article['metrics']:
                        for metric_str in article['metrics'].split(','):
                            try:
                                metric_type, data = metric_str.split(':')
                                value, context = data.split('|')
                                if metric_type not in metrics:
                                    metrics[metric_type] = {
                                        'values': [], 'contexts': []
                                    }
                                metrics[metric_type]['values'].append(float(value))
                                metrics[metric_type]['contexts'].append(context)
                            except:
                                continue
                    article['metrics'] = metrics
                    
                    articles.append(article)

                return articles, total

        except Exception as e:
            self.logger.error(f"Error searching articles: {str(e)}")
            return [], 0

    def close(self):
        """Close database connection"""
        try:
            self.engine.dispose()
        except Exception as e:
            self.logger.error(f"Error closing database connection: {str(e)}")