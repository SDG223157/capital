# app/news/routes.py

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from app.utils.analysis.news_service import NewsAnalysisService
from app.utils.analytics.news_analytics import NewsAnalytics
from datetime import datetime, timedelta
import logging
from http import HTTPStatus

logger = logging.getLogger(__name__)
bp = Blueprint('news', __name__)

# Initialize services
news_service = NewsAnalysisService()

def init_analytics():
    """Initialize analytics with database session"""
    return NewsAnalytics(current_app.db.session)

@bp.route('/')
@login_required
def index():
    """News dashboard home page"""
    try:
        # Set default date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get initial data
        articles, total = news_service.get_articles_by_date_range(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            page=1,
            per_page=10
        )
        
        # Get analytics
        analytics = init_analytics()
        sentiment_analysis = analytics.get_sentiment_analysis(days=7)
        trending_topics = analytics.get_trending_topics(days=7)
        
        return render_template(
            'news/analysis.html',  # Changed from dashboard.html to analysis.html
            articles=articles,
            total_articles=total,
            sentiment_analysis=sentiment_analysis,
            trending_topics=trending_topics,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
    except Exception as e:
        logger.error(f"Error in news index route: {str(e)}", exc_info=True)
        return render_template(
            'news/analysis.html',  # Changed here too
            error="Failed to load news dashboard",
            articles=[],
            total_articles=0,
            sentiment_analysis={},
            trending_topics=[]
        )

@bp.route('/search')
@login_required
def search():
    """Search news articles with filters"""
    try:
        # Get and validate search parameters
        params = _get_search_params()
        logger.debug(f"Processing search with params: {params}")

        # Perform search using search_articles method
        articles, total = news_service.search_articles(
            keyword=params['keyword'],
            symbol=params['symbol'],
            start_date=params['start_date'],
            end_date=params['end_date'],
            sentiment=params['sentiment'],
            page=params['page'],
            per_page=params['per_page']
        )

        # Handle response format
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'articles': articles,
                'total': total,
                'page': params['page'],
                'per_page': params['per_page']
            })
        
        return render_template(
            'news/search.html',
            articles=articles,
            total=total,
            search_params=params
        )
        
    except Exception as e:
        logger.error(f"Error in search route: {str(e)}", exc_info=True)
        error_response = {
            'status': 'error',
            'message': 'Search failed. Please try again.'
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(error_response), HTTPStatus.INTERNAL_SERVER_ERROR
        
        return render_template(
            'news/search.html',
            error=error_response['message'],
            search_params=_get_search_params(),
            articles=[],
            total=0
        )

@bp.route('/api/news/fetch', methods=['POST'])
@login_required
def fetch_news():
    """Fetch and analyze news for specific symbols"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), HTTPStatus.BAD_REQUEST
            
        symbols = data.get('symbols', [])
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), HTTPStatus.BAD_REQUEST
            
        limit = min(int(data.get('limit', 10)), 50)  # Cap limit at 50
        
        logger.info(f"Fetching news for symbols: {symbols}, limit: {limit}")
        articles = news_service.fetch_and_analyze_news(symbols=symbols, limit=limit)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully fetched {len(articles)} articles',
            'articles': articles
        })
        
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch news',
            'error': str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/api/news/sentiment')
@login_required
def get_sentiment():
    """Get sentiment analysis for specified parameters"""
    try:
        analytics = init_analytics()
        
        symbol = request.args.get('symbol')
        days = min(int(request.args.get('days', 7)), 90)  # Cap at 90 days
        include_metrics = request.args.get('include_metrics', 'true').lower() == 'true'
        
        analysis = analytics.get_sentiment_analysis(
            symbol=symbol,
            days=days,
            include_metrics=include_metrics
        )
        
        return jsonify({
            'status': 'success',
            'data': analysis
        })
        
    except Exception as e:
        logger.error(f"Error getting sentiment analysis: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to get sentiment analysis'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/api/news/trending')
@login_required
def get_trending():
    """Get trending topics analysis"""
    try:
        analytics = init_analytics()
        days = min(int(request.args.get('days', 7)), 30)  # Cap at 30 days
        
        topics = analytics.get_trending_topics(days=days)
        
        return jsonify({
            'status': 'success',
            'data': topics
        })
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to get trending topics'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/api/news/correlations')
@login_required
def get_correlations():
    """Get symbol correlations"""
    try:
        analytics = init_analytics()
        
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({
                'status': 'error',
                'message': 'Symbol is required'
            }), HTTPStatus.BAD_REQUEST
            
        days = min(int(request.args.get('days', 30)), 90)  # Cap at 90 days
        
        correlations = analytics.get_symbol_correlations(
            symbol=symbol,
            days=days
        )
        
        return jsonify({
            'status': 'success',
            'data': correlations
        })
        
    except Exception as e:
        logger.error(f"Error getting correlations: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to get correlations'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

def _get_search_params():
    """Extract and validate search parameters from request"""
    now = datetime.now()
    
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, int(request.args.get('per_page', 20)))
    except (TypeError, ValueError):
        page = 1
        per_page = 20

    return {
        'keyword': request.args.get('keyword', '').strip() or None,
        'symbol': request.args.get('symbol', '').strip() or None,
        'start_date': request.args.get('start_date') or (now - timedelta(days=30)).strftime("%Y-%m-%d"),
        'end_date': request.args.get('end_date') or now.strftime("%Y-%m-%d"),
        'sentiment': request.args.get('sentiment', '').strip() or None,
        'page': page,
        'per_page': per_page,
        'include_analytics': request.args.get('include_analytics', 'false').lower() == 'true'
    }

@bp.teardown_request
def cleanup(exception):
    """Cleanup resources after each request"""
    try:
        if hasattr(news_service, 'close'):
            news_service.close()
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")