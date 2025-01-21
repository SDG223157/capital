from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.utils.analysis.news_service import NewsAnalysisService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('news', __name__, url_prefix='/news')

# Initialize news service
news_service = NewsAnalysisService()

@bp.route('/', methods=['GET'])
@login_required
def index():
    """News dashboard home page"""
    try:
        # Get default date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get initial news data
        articles, total = news_service.get_news_by_date_range(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            page=1,
            per_page=10
        )
        
        # Get sentiment summary
        sentiment_summary = news_service.get_sentiment_summary(days=7)
        
        # Get trending topics
        trending_topics = news_service.get_trending_topics()
        
        return render_template(
            'news/analysis.html',
            articles=articles,
            total_articles=total,
            sentiment_summary=sentiment_summary,
            trending_topics=trending_topics
        )
    except Exception as e:
        logger.error(f"Error in news index route: {str(e)}")
        return render_template('news/analysis.html', error="Failed to load news dashboard")

@bp.route('/search', methods=['GET'])
@login_required
def search():
    """Search news articles"""
    logger.debug(f"Search request received with params: {request.args}")
    try:
        # Get search parameters
        keyword = request.args.get('keyword', '').strip()
        symbol = request.args.get('symbol', '').strip()
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        sentiment = request.args.get('sentiment', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Only perform search if we have at least one search parameter
        if any([keyword, symbol, start_date, end_date, sentiment]):
            articles, total = news_service.search_news(
                keyword=keyword,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                sentiment=sentiment,
                page=page,
                per_page=per_page
            )
        else:
            articles, total = [], 0
            
        # Prepare search parameters for template
        search_params = {
            'keyword': keyword,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'sentiment': sentiment,
            'page': page,
            'per_page': per_page
        }
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'articles': articles,
                'total': total,
                'page': page,
                'per_page': per_page
            })
            
        # Handle regular requests
        return render_template(
            'news/search.html',
            articles=articles,
            total=total,
            search_params=search_params
        )
    except Exception as e:
        logger.error(f"Error in search route: {str(e)}", exc_info=True)
        error_response = {'status': 'error', 'message': 'Search failed. Please try again.'}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(error_response), 500
        return render_template('news/search.html', error=error_response['message'])
    except Exception as e:
        logger.error(f"Error in news search route: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@bp.route('/api/sentiment', methods=['GET'])
@login_required
def get_sentiment():
    """Get sentiment analysis summary"""
    try:
        date = request.args.get('date')
        symbol = request.args.get('symbol')
        days = int(request.args.get('days', 7))
        
        summary = news_service.get_sentiment_summary(
            date=date,
            symbol=symbol,
            days=days
        )
        
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {str(e)}")
        return jsonify({'error': 'Failed to get sentiment summary'}), 500

@bp.route('/api/trending', methods=['GET'])
@login_required
def get_trending():
    """Get trending topics"""
    try:
        days = int(request.args.get('days', 7))
        topics = news_service.get_trending_topics(days=days)
        return jsonify(topics)
    except Exception as e:
        logger.error(f"Error getting trending topics: {str(e)}")
        return jsonify({'error': 'Failed to get trending topics'}), 500

@bp.route('/api/fetch', methods=['POST'])
@login_required
def fetch_news():
    """Manually trigger news fetch for specific symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        limit = int(data.get('limit', 10))
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
            
        articles = news_service.fetch_and_analyze_news(
            symbols=symbols,
            limit=limit
        )
        
        return jsonify({
            'message': f'Successfully fetched {len(articles)} articles',
            'articles': articles
        })
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        return jsonify({'error': 'Failed to fetch news'}), 500

@bp.teardown_app_request
def cleanup(exception):
    """Cleanup resources after each request"""
    try:
        if hasattr(news_service, 'close'):
            news_service.close()
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        
# Add this to your routes.py temporarily for testing

@bp.route('/test-fetch', methods=['GET'])
@login_required
def test_fetch():
    """Test endpoint to fetch and store news"""
    try:
        logger.debug("Starting news fetch test...")
        
        # Check if API token is configured
        if not hasattr(news_service.analyzer, 'client') or not news_service.analyzer.client:
            logger.error("API client not properly initialized")
            return jsonify({'error': 'API client not configured'}), 500
            
        # Fetch news for Apple
        logger.debug("Attempting to fetch news for NASDAQ:AAPL")
        articles = news_service.fetch_and_analyze_news(
            symbols=["NASDAQ:AAPL"],
            limit=10
        )
        
        logger.debug(f"Fetch complete. Articles retrieved: {len(articles)}")
        if articles:
            logger.debug(f"Sample article title: {articles[0].get('title', 'No title')}")
        
        return jsonify({
            'message': f'Successfully fetched {len(articles)} articles',
            'articles': articles
        })
    except Exception as e:
        logger.error(f"Error in test fetch: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
# In app/news/routes.py

@bp.route('/test')
def test():
    return 'News blueprint is working!'
# Add this to your routes.py

@bp.route('/debug-routes')
def debug_routes():
    """List all registered routes"""
    output = []
    for rule in bp.url_map.iter_rules():
        output.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule)
        })
    return jsonify(output)