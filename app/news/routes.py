from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.utils.analysis.analysis_service import NewsAnalysisService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('news', __name__, url_prefix='/news')

# Create blueprint
# bp = Blueprint('main', __name__)
# logger = logging.getLogger(__name__)

# @bp.route('/')
# @login_required
# def index():
#     return render_template('index.html')
# app/routes.py

@bp.route('/<symbol>/fetch')
@login_required
def fetch_news(symbol):
    try:
        # days = request.args.get('days', default=5, type=int)

        news_service = NewsAnalysisService()
        # symbols = [symbol]
        try:
            # end_date = datetime.now()
            # start_date = end_date - timedelta(days=days)
            
            # Get news data
            articles = news_service.get_news(
                symbols=[symbol],
                limit=3
               
            )
            formatted_articles = news_service.format_articles(articles)
            logger.info(f"Symbols: {[symbol]}")
            logger.info(f"Articles: {formatted_articles}")

            return jsonify(formatted_articles)

        except Exception as e:
            logger.error(f"Error getting news: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error in fetch_news view: {str(e)}")
        return jsonify({"error": "Failed to fetch news"}), 500

@bp.route('/<symbol>')
@login_required
def news_analysis(symbol):
    try:
        days = request.args.get('days', default=7, type=int)
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)

        news_service = NewsAnalysisService()
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            result = news_service.get_news_analysis(symbol, days)
            articles, total_count = news_service.get_news_by_date_range(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                symbol=symbol,
                page=page,
                per_page=per_page
            )

            total_pages = (total_count + per_page - 1) // per_page

            return render_template(
                'news/analysis.html',
                symbol=symbol,
                days=days,
                summary=result['summary'],
                articles=articles,
                chart_data=result.get('chart_data', {}),
                pagination={
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            )
        finally:
            news_service.close()

    except Exception as e:
        logger.error(f"Error in news analysis view: {str(e)}")
        return render_template('error.html', error="Failed to analyze news data")

@bp.route('/<symbol>/timeline')
@login_required
def news_sentiment_timeline(symbol):
    try:
        days = request.args.get('days', default=7, type=int)
        news_service = NewsAnalysisService()
        try:
            result = news_service.get_news_analysis(symbol, days)
            return jsonify(result.get('chart_data', {}))
        finally:
            news_service.close()
    except Exception as e:
        logger.error(f"Error getting sentiment timeline: {str(e)}")
        return jsonify({"error": "Failed to get sentiment timeline"}), 500

@bp.route('/<symbol>/analysis')
@login_required
def news_analysis_data(symbol):
    try:
        days = request.args.get('days', default=7, type=int)
        news_service = NewsAnalysisService()
        try:
            result = news_service.get_news_analysis(symbol, days)
            return jsonify(result)
        finally:
            news_service.close()
    except Exception as e:
        logger.error(f"Error getting news analysis: {str(e)}")
        return jsonify({"error": "Failed to get news analysis"}), 500

@bp.route('/search')
@login_required
def search_news():
    try:
        symbol = request.args.get('symbol', '')
        keyword = request.args.get('keyword', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)

        news_service = NewsAnalysisService()
        try:
            articles, total_count = news_service.search_articles(
                keyword=keyword,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                page=page,
                per_page=per_page
            )

            return jsonify({
                'articles': articles,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            })
        finally:
            news_service.close()
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        return jsonify({"error": "Failed to search news"}), 500

@bp.route('/<symbol>/export')
@login_required
def export_news(symbol):
    try:
        format_type = request.args.get('format', 'json')
        days = request.args.get('days', default=7, type=int)
        
        news_service = NewsAnalysisService()
        try:
            result = news_service.get_news_analysis(symbol, days)
            if format_type == 'csv':
                return news_service.export_to_csv(result)
            return jsonify(result)
        finally:
            news_service.close()
    except Exception as e:
        logger.error(f"Error exporting news: {str(e)}")
        return jsonify({"error": "Failed to export news"}), 500

@bp.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@bp.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200