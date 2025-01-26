# app/news/routes.py

import os
import re
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from app.utils.analysis.news_service import NewsAnalysisService
from app.utils.analytics.news_analytics import NewsAnalytics
from datetime import datetime, timedelta
import logging
from http import HTTPStatus
# from app import admin_required
from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import NewsArticle
from openai import OpenAI
from app import db
import httpx
# from app.utils.config.news_config import DEFAULT_SYMBOLS
import time
logger = logging.getLogger(__name__)
bp = Blueprint('news', __name__)


# Initialize services
news_service = NewsAnalysisService()

DEFAULT_SYMBOLS = [
    "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL", "NASDAQ:META",
    "NASDAQ:NVDA", "NASDAQ:TSLA", "NYSE:BRK.A", "NYSE:V", "NYSE:JPM",
    "NYSE:JNJ", "NYSE:WMT", "NYSE:MA", "NYSE:PG", "NASDAQ:AVGO",
    "NYSE:CVX", "NYSE:HD", "NYSE:MRK", "NYSE:KO", "NASDAQ:PEP", 
    "NYSE:BAC", "NYSE:DIS", "NASDAQ:COST", "NASDAQ:CSCO", "NYSE:VZ",
    "NYSE:ABT", "NASDAQ:ADBE", "NASDAQ:CMCSA", "NYSE:NKE", "NYSE:TMO"
    ]

def init_analytics():
    """Initialize analytics with database session"""
    return NewsAnalytics(current_app.db.session)

@bp.route('/')
@login_required
def index():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        articles, total = news_service.get_articles_by_date_range(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            page=1,
            per_page=10
        )
        
        sentiment_summary = news_service.get_sentiment_summary(days=7)
        sentiment_summary['total_articles'] = total  # Ensure total_articles is set
        
        return render_template(
            'news/analysis.html',
            articles=articles,
            total_articles=total,
            sentiment_summary=sentiment_summary,
            trending_topics=[],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
    except Exception as e:
        logger.error(f"Error in news index route: {str(e)}", exc_info=True)
        return render_template(
            'news/analysis.html',
            error="Failed to load news dashboard",
            articles=[],
            total_articles=0,
            sentiment_summary={'total_articles': 0, 'average_sentiment': 0},
            trending_topics=[]
        )
@bp.route('/fetch')
@login_required
def fetch():
    """Render the Fetch News page"""
    return render_template('news/fetch.html')

@bp.route('/search')
@login_required
def search():
    try:
        symbol = request.args.get('symbol')
        symbol = None if symbol in ['None', '', None] else symbol
        
        # Return no articles if no symbol is provided
        if not symbol:
            return render_template(
                'news/search.html',
                articles=[],
                total=0,
                search_params={'symbol': symbol}
            )
        
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, int(request.args.get('per_page', 20)))

        articles, total = news_service.search_articles(
            symbol=symbol,
            page=page,
            per_page=per_page
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success',
                'articles': articles,
                'total': total
            })
        
        return render_template(
            'news/search.html',
            articles=articles,
            total=total,
            search_params={'symbol': symbol}
        )
        
    except Exception as e:
        logger.error(f"Error in search route: {str(e)}", exc_info=True)
        error_msg = 'Search failed. Please try again.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': error_msg}), 500
        
        return render_template(
            'news/search.html',
            error=error_msg,
            articles=[],
            total=0,
            search_params={'symbol': symbol}
        )

@bp.route('/api/fetch', methods=['POST'])
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
        
        
# Add at top level of routes.py
# DEFAULT_SYMBOLS = [
#    "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL", "NASDAQ:META",
#    "NASDAQ:NVDA", "NASDAQ:TSLA", "NYSE:BRK.A", "NYSE:V", "NYSE:JPM",
#    "NYSE:JNJ", "NYSE:WMT", "NYSE:MA", "NYSE:PG", "NASDAQ:AVGO",
#    "NYSE:CVX", "NYSE:HD", "NYSE:MRK", "NYSE:KO", "NASDAQ:PEP", 
#    "NYSE:BAC", "NYSE:DIS", "NASDAQ:COST", "NASDAQ:CSCO", "NYSE:VZ",
#    "NYSE:ABT", "NASDAQ:ADBE", "NASDAQ:CMCSA", "NYSE:NKE", "NYSE:TMO"
# ]
@bp.route('/api/batch-fetch', methods=['POST'])
@login_required
def batch_fetch():
    try:
        data = request.get_json()
        chunk_size = 5  # Process 5 symbols at a time
        symbols = data.get('symbols', DEFAULT_SYMBOLS[:10]) 
        articles_per_symbol = min(int(data.get('limit', 2)), 5)
        
        all_articles = []
        chunks = [symbols[i:i + chunk_size] for i in range(0, len(symbols), chunk_size)]
        
        for chunk in chunks:
            for symbol in chunk:
                try:
                    articles = news_service.fetch_and_analyze_news(
                        symbols=[symbol], 
                        limit=articles_per_symbol
                    )
                    all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {str(e)}")
                    continue
                
        return jsonify({
            'status': 'success',
            'articles': all_articles,
            'total': len(all_articles)
        })
        
    except Exception as e:
        logger.error(f"Batch fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    

@bp.route('/api/update-summaries', methods=['POST'])
@login_required
def update_ai_summaries():
   try:
       client = OpenAI(
           api_key=os.getenv('DEEPSEEK_API_KEY'),
           base_url="https://api.deepseek.com",
           timeout=120.0
       )
       
       articles = NewsArticle.query.filter(
           db.or_(
               NewsArticle.ai_summary.is_(None),
               NewsArticle.ai_insights.is_(None)
           ),
           NewsArticle.content.isnot(None)
       ).limit(10).all()
       
       processed = 0
       
       for article in articles:
           try:
               if article.ai_summary is None:
                   summary_response = client.chat.completions.create(
                       model="deepseek-chat",
                       messages=[
                           {"role": "system", "content": "Generate a concise summary of this news article."},
                           {"role": "user", "content": article.content}
                       ],
                       max_tokens=250
                   )
                   article.ai_summary = summary_response.choices[0].message.content

               if article.ai_insights is None:
                   insights_response = client.chat.completions.create(
                       model="deepseek-chat",
                       messages=[
                           {"role": "system", "content": "Extract key financial insights and implications from this article."},
                           {"role": "user", "content": article.content}
                       ],
                       max_tokens=250
                   )
                   article.ai_insights = insights_response.choices[0].message.content

               db.session.commit()
               processed += 1
               
           except Exception as e:
               logger.error(f"Error processing article {article.id}: {str(e)}")
               db.session.rollback()
               continue
               
       return jsonify({
           'status': 'success',
           'message': f'Successfully processed {processed} articles',
           'total_processed': processed
       })
       
   except Exception as e:
       logger.error(f"Error updating AI summaries: {str(e)}")
       return jsonify({'status': 'error', 'message': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
@bp.route('/api/sentiment')
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

@bp.route('/api/trending')
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

# @bp.route('/api/news/sentiment')
# @login_required
# def get_sentiment():
#     """Get sentiment analysis for specified parameters"""
#     try:
#         analytics = init_analytics()
        
#         symbol = request.args.get('symbol')
#         days = min(int(request.args.get('days', 7)), 90)  # Cap at 90 days
#         include_metrics = request.args.get('include_metrics', 'true').lower() == 'true'
        
#         analysis = analytics.get_sentiment_analysis(
#             symbol=symbol,
#             days=days,
#             include_metrics=include_metrics
#         )
        
#         return jsonify({
#             'status': 'success',
#             'data': analysis
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting sentiment analysis: {str(e)}", exc_info=True)
#         return jsonify({
#             'status': 'error',
#             'message': 'Failed to get sentiment analysis'
#         }), HTTPStatus.INTERNAL_SERVER_ERROR

# @bp.route('/api/news/trending')
# @login_required
# def get_trending():
#     """Get trending topics analysis"""
#     try:
#         analytics = init_analytics()
#         days = min(int(request.args.get('days', 7)), 30)  # Cap at 30 days
        
#         topics = analytics.get_trending_topics(days=days)
        
#         return jsonify({
#             'status': 'success',
#             'data': topics
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting trending topics: {str(e)}", exc_info=True)
#         return jsonify({
#             'status': 'error',
#             'message': 'Failed to get trending topics'
#         }), HTTPStatus.INTERNAL_SERVER_ERROR

# @bp.route('/api/news/correlations')
# @login_required
# def get_correlations():
#     """Get symbol correlations"""
#     try:
#         analytics = init_analytics()
        
#         symbol = request.args.get('symbol')
#         if not symbol:
#             return jsonify({
#                 'status': 'error',
#                 'message': 'Symbol is required'
#             }), HTTPStatus.BAD_REQUEST
            
#         days = min(int(request.args.get('days', 30)), 90)  # Cap at 90 days
        
#         correlations = analytics.get_symbol_correlations(
#             symbol=symbol,
#             days=days
#         )
        
#         return jsonify({
#             'status': 'success',
#             'data': correlations
#         })
        
#     except Exception as e:
#         logger.error(f"Error getting correlations: {str(e)}", exc_info=True)
#         return jsonify({
#             'status': 'error',
#             'message': 'Failed to get correlations'
#         }), HTTPStatus.INTERNAL_SERVER_ERROR

def _get_search_params():
    """Extract and validate search parameters from request"""
    now = datetime.now()
    
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, int(request.args.get('per_page', 20)))
    except (TypeError, ValueError):
        page = 1
        per_page = 20

    keyword = request.args.get('keyword')
    keyword = None if keyword in ['None', '', None] else keyword

    symbol = request.args.get('symbol')
    symbol = None if symbol in ['None', '', None] else symbol

    return {
        'keyword': keyword,
        'symbol': symbol,
        'start_date': request.args.get('start_date') or (now - timedelta(days=30)).strftime("%Y-%m-%d"),
        'end_date': request.args.get('end_date') or now.strftime("%Y-%m-%d"),
        'sentiment': request.args.get('sentiment') or None,
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
        
@bp.route('/api/symbol-suggest')
@login_required
def symbol_suggest():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'suggestions': []})
    
    suggested_symbol = get_tradingview_symbol(symbol)
    return jsonify({'suggestions': [{'symbol': suggested_symbol}]})

def get_tradingview_symbol(symbol):
    """Convert stock symbol to TradingView format"""
    symbol = symbol.upper()
    
    # Common NASDAQ stocks
    nasdaq_stocks = {
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'META', 'NVDA', 'TSLA', 'AVGO', 
        'ADBE', 'CSCO', 'INTC', 'QCOM', 'AMD', 'INTU', 'AMAT', 'MU', 'NFLX', 'PEP'
    }
    
    # Hong Kong stocks
    if re.match(r'^\d{4}\.HK$', symbol, re.IGNORECASE):
        return f"HKEX:{symbol.replace('.HK', '').replace('.hk', '')}"
    elif symbol.startswith('0') and re.search(r'\.HK$', symbol, re.IGNORECASE):
        return f"HKEX:{symbol.replace('0', '').replace('.HK', '').replace('.hk', '')}"
        
    # Shanghai stocks
    elif re.search(r'\.SS$', symbol, re.IGNORECASE):
        return f"SSE:{symbol.replace('.SS', '').replace('.ss', '')}"
    
    # NASDAQ stocks
    elif symbol in nasdaq_stocks:
        return f"NASDAQ:{symbol}"
    elif symbol.endswith('.O'):
        return f"NASDAQ:{symbol.replace('.O', '')}"
        
    # Default to NYSE
    return f"NYSE:{symbol}"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # HTTP 403 Forbidden
        return f(*args, **kwargs)
    return decorated_function