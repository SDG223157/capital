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
# Add to top of file
import requests
from http import HTTPStatus
import re
# Consider adding rate limiting decorator
from flask_limiter import Limiter
limiter = Limiter(app=current_app, key_func=lambda: current_user.id)
# import httpx
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
# DEFAULT_SYMBOLS = [
#     "HKEX:0700", "HKEX:9988", "HKEX:1299", "HKEX:0941", "HKEX:0388",
#     "HKEX:0005", "HKEX:3690", "HKEX:2318", "HKEX:2628", "HKEX:1211",
#     "HKEX:1810", "HKEX:2382", "HKEX:1024", "HKEX:9618", "HKEX:2269",
#     "HKEX:2018", "HKEX:2020", "HKEX:1177", "HKEX:1928", "HKEX:0883",
#     "HKEX:1088", "HKEX:0857", "HKEX:0386", "HKEX:0001", "HKEX:0016",
#     "HKEX:0011", "HKEX:0002", "HKEX:0003", "HKEX:0006", "HKEX:0012",
#     "HKEX:0017", "HKEX:0019", "HKEX:0066", "HKEX:0083", "HKEX:0101",
#     "HKEX:0135", "HKEX:0151", "HKEX:0175", "HKEX:0267", "HKEX:0288",
#     "HKEX:0291", "HKEX:0293", "HKEX:0330", "HKEX:0392", "HKEX:0688",
#     "HKEX:0762", "HKEX:0823", "HKEX:0960", "HKEX:1038", "HKEX:1109"
# ]

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
    
def initialize_articles() -> None:
    """Initialize all articles by setting AI fields to None"""
    try:
        articles_updated = NewsArticle.query.update({
            NewsArticle.ai_summary: None,
            NewsArticle.ai_insights: None,
            NewsArticle.ai_sentiment_rating: None
        })
        db.session.commit()
        logger.info(f"Initialized {articles_updated} articles with None values")
    except Exception as e:
        logger.error(f"Error initializing articles: {str(e)}")
        db.session.rollback()
        raise      
@bp.route('/api/get-articles-to-update', methods=['GET'])
@login_required
def get_articles_to_update():
    try:
        # Fetch the articles that need to be updated
        articles = NewsArticle.query.filter(
            db.or_(
                NewsArticle.ai_summary.is_(None),
                NewsArticle.ai_insights.is_(None),
                NewsArticle.ai_sentiment_rating.is_(None)
            ),
            NewsArticle.content.isnot(None)
        ).all()

        # Return the count of articles to be updated
        return jsonify({
            'status': 'success',
            'count': len(articles)
        })
    except Exception as e:
        logger.error(f"Error getting articles to update: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@bp.route('/api/latest-articles-wrapup', methods=['GET'])
@login_required
def get_latest_articles_wrapup():
    try:
        # Fetch the latest 10 articles
        articles = NewsArticle.query.order_by(NewsArticle.published_at.desc()).limit(10).all()

        wrapup_results = []

        for article in articles:
            wrapup_results.append({
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'published_at': article.published_at.strftime("%Y-%m-%d %H:%M:%S"),
                'wrapup': article.brief_summary or "No summary available."  # Use brief_summary
            })

        return jsonify({
            'status': 'success',
            'articles': wrapup_results
        })

    except Exception as e:
        logger.error(f"Error in get_latest_articles_wrapup: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/api/update-summaries', methods=['POST'])
@login_required
def update_ai_summaries():
    """Update news articles using OpenRouter API with dynamic prompt selection"""
    
    # =====================
    # PROMPT BANK CONFIGURATION
    # =====================
    PROMPT_BANK = {
        'summary': [
            {
                'id': 1,
                'name': 'Concise Summary',
                'instruction': "Summarize the main points in 3-5 bullet points focusing on key stakeholders and "
                               "financial implications. Use markdown formatting. Avoid technical jargon.",
                'model': "anthropic/claude-3.5-sonnet",
                'condition': lambda c: 500 < len(c) < 2000
            },
            {
                'id': 6,
                'name': 'Executive TL;DR',
                'instruction': "Create an executive summary highlighting: 1) Core event 2) Market impact "
                               "3) Key players 4) Potential outcomes. Use bold headers for each section.",
                'model': "google/palm-2",
                'condition': lambda c: len(c) >= 2000
            }
        ],
        'insights': [
            {
                'id': 3,
                'name': 'Investor Focus',
                'instruction': "Identify 3-5 actionable insights for investors including: - Short-term opportunities "
                               "- Long-term risks - Sector implications - Recommended watchlist symbols",
                'model': "anthropic/claude-3.5-sonnet",
                'condition': lambda c: any(kw in c.lower() for kw in ['stock', 'share', 'investment', 'market'])
            },
            {
                'id': 15,
                'name': 'Policy Impact',
                'instruction': "Analyze regulatory/policy impacts including: - Affected industries - Compliance costs "
                               "- Potential market shifts - Timeline implications",
                'model': "meta-llama/llama-3-70b",
                'condition': lambda c: any(kw in c.lower() for kw in ['regulation', 'policy', 'law', 'compliance'])
            }
        ],
        'sentiment': [
            {
                'id': 11,
                'name': 'Multi-dimensional Sentiment',
                'instruction': "Evaluate sentiment through three lenses:\n1. Market impact (scale: -100 to 100)\n"
                               "2. Retail investor perception\n3. Institutional reaction\nFormat: Market:<score>|"
                               "Retail:<score>|Institutions:<score>",
                'model': "anthropic/claude-3.5-sonnet",
                'condition': lambda _: True
            }
        ]
    }

    # =====================
    # HELPER FUNCTIONS
    # =====================
    def select_prompt(content, prompt_type):
        """Select the most appropriate prompt based on content analysis"""
        try:
            for prompt in PROMPT_BANK[prompt_type]:
                if prompt['condition'](content):
                    return {
                        'id': prompt['id'],
                        'name': prompt['name'],
                        'instruction': prompt['instruction'],
                        'model': prompt['model']
                    }
            return PROMPT_BANK[prompt_type][0]  # Fallback to first prompt
        except Exception as e:
            logger.error(f"Prompt selection error: {str(e)}")
            return PROMPT_BANK[prompt_type][0]

    def parse_sentiment_response(response):
        """Parse and normalize sentiment response into aggregate score"""
        try:
            market = int(re.search(r"Market:(-?\d+)", response).group(1))
            retail = int(re.search(r"Retail:(-?\d+)", response).group(1))
            institutions = int(re.search(r"Institutions:(-?\d+)", response).group(1))
            return int((market * 0.6) + (retail * 0.2) + (institutions * 0.2))
        except Exception as e:
            logger.warning(f"Sentiment parsing failed: {str(e)}")
            return 0

    # =====================
    # MAIN PROCESSING LOGIC
    # =====================
    try:
        # OpenRouter API configuration
        OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
        BASE_URL = "https://openrouter.ai/api/v1"
        HEADERS = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://your-domain.com",  # Required by OpenRouter
            "X-Title": "Financial News Analyzer"
        }

        # Fetch articles needing processing
        articles = NewsArticle.query.filter(
            db.or_(
                NewsArticle.ai_summary.is_(None),
                NewsArticle.ai_insights.is_(None),
                NewsArticle.ai_sentiment_rating.is_(None)
            ),
            NewsArticle.content.isnot(None)
        ).order_by(NewsArticle.published_at.desc()).limit(5).all()  # Reduced batch size for stability

        processed = 0
        results = []

        for article in articles:
            try:
                content = article.content
                prompts_used = {}

                # --- Summary Generation ---
                if not article.ai_summary:
                    summary_prompt = select_prompt(content, 'summary')
                    prompts_used['summary'] = summary_prompt
                    
                    response = requests.post(
                        f"{BASE_URL}/chat/completions",
                        headers=HEADERS,
                        json={
                            "model": summary_prompt['model'],
                            "messages": [
                                {"role": "system", "content": summary_prompt['instruction']},
                                {"role": "user", "content": f"Article content:\n{content}"}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 500
                        },
                        timeout=45
                    )
                    response.raise_for_status()
                    article.ai_summary = response.json()['choices'][0]['message']['content']

                # --- Insights Generation ---
                if not article.ai_insights:
                    insights_prompt = select_prompt(content, 'insights')
                    prompts_used['insights'] = insights_prompt
                    
                    response = requests.post(
                        f"{BASE_URL}/chat/completions",
                        headers=HEADERS,
                        json={
                            "model": insights_prompt['model'],
                            "messages": [
                                {"role": "system", "content": insights_prompt['instruction']},
                                {"role": "user", "content": f"Article content:\n{content}"}
                            ],
                            "temperature": 0.5,
                            "max_tokens": 600
                        },
                        timeout=60
                    )
                    response.raise_for_status()
                    article.ai_insights = response.json()['choices'][0]['message']['content']

                # --- Sentiment Analysis ---
                if article.ai_sentiment_rating is None:
                    sentiment_prompt = select_prompt(content, 'sentiment')
                    prompts_used['sentiment'] = sentiment_prompt
                    
                    response = requests.post(
                        f"{BASE_URL}/chat/completions",
                        headers=HEADERS,
                        json={
                            "model": sentiment_prompt['model'],
                            "messages": [
                                {"role": "system", "content": sentiment_prompt['instruction']},
                                {"role": "user", "content": f"Article content:\n{content}"}
                            ],
                            "temperature": 0.2,
                            "max_tokens": 150
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    raw_sentiment = response.json()['choices'][0]['message']['content']
                    article.ai_sentiment_rating = parse_sentiment_response(raw_sentiment)

                # Commit changes
                db.session.commit()
                processed += 1
                
                # Store processing metadata
                results.append({
                    'id': article.id,
                    'title': article.title[:75] + '...' if len(article.title) > 75 else article.title,
                    'sentiment': article.ai_sentiment_rating,
                    'prompts': prompts_used,
                    'models_used': {k: v['model'] for k,v in prompts_used.items()},
                    'processing_time': datetime.now().isoformat()
                })

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for article {article.id}: {str(e)}")
                db.session.rollback()
                continue
            except Exception as e:
                logger.error(f"General processing error for article {article.id}: {str(e)}")
                db.session.rollback()
                continue

        return jsonify({
            'status': 'success',
            'processed': processed,
            'batch_size': len(articles),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Critical system error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': "Article processing system unavailable",
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
# @bp.route('/api/update-summaries', methods=['POST'])
# @login_required
# def update_ai_summaries():
#     try:
#         client = OpenAI(
#             api_key=os.getenv('DEEPSEEK_API_KEY'),
#             base_url="https://api.deepseek.com",
#             timeout=120.0
#         )
        
#         articles = NewsArticle.query.filter(
#             db.or_(
#                 NewsArticle.ai_summary.is_(None),
#                 NewsArticle.ai_insights.is_(None),
#                 NewsArticle.ai_sentiment_rating.is_(None)
#             ),
#             NewsArticle.content.isnot(None)
#         ).limit(10).all()
        
#         processed = 0
#         results = []
        
#         for article in articles:
#             try:
#                 if not article.ai_summary:
#                     summary_response = client.chat.completions.create(
#                         model="deepseek-chat",
#                         messages=[
#                             {"role": "system", "content": "Generate a concise summary of this news article."},
#                             {"role": "user", "content": article.content}
#                         ],
#                         max_tokens=250
#                     )
#                     article.ai_summary = summary_response.choices[0].message.content

#                 if not article.ai_insights:
#                     insights_response = client.chat.completions.create(
#                         model="deepseek-chat",
#                         messages=[
#                             {"role": "system", "content": "Extract key financial insights and implications from this article."},
#                             {"role": "user", "content": article.content}
#                         ],
#                         max_tokens=250
#                     )
#                     article.ai_insights = insights_response.choices[0].message.content

#                 if article.ai_sentiment_rating is None:
#                     sentiment_response = client.chat.completions.create(
#                         model="deepseek-chat",
#                         messages=[
#                             {"role": "system", "content": "Analyze the sentiment of this article and provide a rating from -100 (extremely negative) to 100 (extremely positive). Return only the number."},
#                             {"role": "user", "content": article.content}
#                         ],
#                         max_tokens=10
#                     )
#                     try:
#                         rating = int(sentiment_response.choices[0].message.content.strip())
#                         # Ensure rating is within bounds
#                         article.ai_sentiment_rating = max(min(rating, 100), -100)
#                     except ValueError:
#                         logger.error(f"Could not parse sentiment rating for article {article.id}")
#                         article.ai_sentiment_rating = 0

#                 db.session.commit()
#                 processed += 1
#                 results.append({
#                     'id': article.id, 
#                     'title': article.title,
#                     'ai_sentiment_rating': article.ai_sentiment_rating
#                 })
                
#             except Exception as e:
#                 logger.error(f"Error processing article {article.id}: {str(e)}")
#                 db.session.rollback()
#                 continue
                
#         return jsonify({
#             'status': 'success',
#             'processed': processed,
#             'articles': results
#         })
        
#     except Exception as e:
#         logger.error(f"Error: {str(e)}")
#         return jsonify({'status': 'error', 'message': str(e)}), 500


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