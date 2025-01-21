# app/utils/analytics/news_analytics.py

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ...models import NewsArticle, ArticleSymbol, ArticleMetric
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from textblob import TextBlob

class NewsAnalytics:
    def __init__(self, session: Session):
        self.session = session

    def get_sentiment_analysis(self, symbol: str, days: int = 30) -> Dict:
        """Get detailed sentiment analysis for a symbol"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Get all relevant articles
        articles = (
            self.session.query(NewsArticle)
            .join(ArticleSymbol)
            .filter(
                ArticleSymbol.symbol == symbol,
                NewsArticle.published_at >= start_date
            )
            .all()
        )
        
        if not articles:
            return {}
            
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'date': article.published_at,
            'sentiment_score': article.sentiment_score,
            'sentiment_label': article.sentiment_label
        } for article in articles])
        
        # Calculate metrics
        analysis = {
            'total_articles': len(articles),
            'sentiment_distribution': {
                'positive': len(df[df['sentiment_label'] == 'POSITIVE']),
                'negative': len(df[df['sentiment_label'] == 'NEGATIVE']),
                'neutral': len(df[df['sentiment_label'] == 'NEUTRAL'])
            },
            'average_sentiment': float(df['sentiment_score'].mean()),
            'sentiment_volatility': float(df['sentiment_score'].std()),
            'trend': self._calculate_trend(df)
        }
        
        # Add moving averages
        df['MA5'] = df['sentiment_score'].rolling(window=5).mean()
        df['MA10'] = df['sentiment_score'].rolling(window=10).mean()
        
        analysis['moving_averages'] = {
            'MA5': df['MA5'].dropna().tolist(),
            'MA10': df['MA10'].dropna().tolist()
        }
        
        return analysis

    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """Calculate sentiment trend"""
        if len(df) < 2:
            return "Insufficient data"
            
        # Calculate linear regression
        x = np.arange(len(df))
        y = df['sentiment_score'].values
        z = np.polyfit(x, y, 1)
        slope = z[0]
        
        if slope > 0.01:
            return "Improving"
        elif slope < -0.01:
            return "Declining"
        else:
            return "Stable"

    def get_entity_correlation(self, symbol: str, days: int = 30) -> Dict[str, List[Dict]]:
        """Analyze correlations between entities and sentiment"""
        start_date = datetime.now() - timedelta(days=days)
        
        articles = (
            self.session.query(NewsArticle)
            .join(ArticleSymbol)
            .filter(
                ArticleSymbol.symbol == symbol,
                NewsArticle.published_at >= start_date
            )
            .all()
        )
        
        entities = {
            'companies': {},
            'people': {},
            'metrics': {}
        }
        
        for article in articles:
            sentiment = article.sentiment_score
            blob = TextBlob(article.content)
            
            # Analyze noun phrases
            for phrase in blob.noun_phrases:
                if self._is_company(phrase):
                    self._update_correlation(
                        entities['companies'], 
                        phrase, 
                        sentiment
                    )
                elif self._is_person(phrase):
                    self._update_correlation(
                        entities['people'], 
                        phrase, 
                        sentiment
                    )
            
            # Analyze metrics
            for metric in article.metrics:
                self._update_correlation(
                    entities['metrics'],
                    f"{metric.metric_type}:{metric.value}",
                    sentiment
                )
        
        # Process and sort correlations
        return {
            category: self._process_correlations(correlations)
            for category, correlations in entities.items()
        }

    def _update_correlation(self, data: Dict, key: str, sentiment: float):
        """Update correlation data"""
        if key not in data:
            data[key] = {
                'count': 0,
                'sentiment_sum': 0,
                'sentiment_squares': 0
            }
        
        data[key]['count'] += 1
        data[key]['sentiment_sum'] += sentiment
        data[key]['sentiment_squares'] += sentiment * sentiment

    def _process_correlations(self, correlations: Dict) -> List[Dict]:
        """Process raw correlation data"""
        results = []
        for key, data in correlations.items():
            if data['count'] >= 3:  # Minimum threshold
                avg_sentiment = data['sentiment_sum'] / data['count']
                variance = (
                    data['sentiment_squares'] / data['count'] - 
                    avg_sentiment * avg_sentiment
                )
                
                results.append({
                    'entity': key,
                    'occurrences': data['count'],
                    'avg_sentiment': avg_sentiment,
                    'volatility': np.sqrt(max(0, variance))
                })
        
        return sorted(results, key=lambda x: x['occurrences'], reverse=True)

    def get_topic_impact(self, symbol: str, topic: str, days: int = 30) -> Dict:
        """Analyze the impact of a specific topic on sentiment"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Get articles with and without the topic
        with_topic = set(
            article.id for article in
            self.session.query(NewsArticle.id)
            .join(ArticleSymbol)
            .filter(
                ArticleSymbol.symbol == symbol,
                NewsArticle.published_at >= start_date,
                or_(
                    NewsArticle.content.ilike(f'%{topic}%'),
                    NewsArticle.title.ilike(f'%{topic}%')
                )
            )
        )
        
        all_articles = (
            self.session.query(NewsArticle)
            .join(ArticleSymbol)
            .filter(
                ArticleSymbol.symbol == symbol,
                NewsArticle.published_at >= start_date
            )
        )
        
        without_topic = set(article.id for article in all_articles) - with_topic
        
        # Calculate statistics
        topic_stats = self._calculate_stats(with_topic)
        baseline_stats = self._calculate_stats(without_topic)
        
        return {
            'topic_stats': topic_stats,
            'baseline_stats': baseline_stats,
            'impact': {
                'sentiment_difference': topic_stats['avg_sentiment'] - baseline_stats['avg_sentiment'],
                'relative_frequency': len(with_topic) / (len(with_topic) + len(without_topic))
            }
        }

    def _calculate_stats(self, article_ids: set) -> Dict:
        """Calculate statistics for a set of articles"""
        if not article_ids:
            return {
                'count': 0,
                'avg_sentiment': 0,
                'sentiment_std': 0
            }
            
        articles = (
            self.session.query(NewsArticle)
            .filter(NewsArticle.id.in_(article_ids))
        )
        
        sentiments = [article.sentiment_score for article in articles]
        
        return {
            'count': len(sentiments),
            'avg_sentiment': np.mean(sentiments),
            'sentiment_std': np.std(sentiments) if len(sentiments) > 1 else 0
        }