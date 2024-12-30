from flask import Blueprint, render_template, request, make_response, jsonify, redirect, url_for
from datetime import datetime
import yfinance as yf
import logging
import sys
import re
import os
import traceback
from flask_login import login_required, current_user
from app.utils.analyzer.stock_analyzer import create_stock_visualization
from sqlalchemy import inspect
from app import db
from sqlalchemy import text
from flask import send_file
import pandas as pd
import io

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create Blueprint
bp = Blueprint('main', __name__)

def verify_ticker(symbol):
    """Verify ticker with yfinance and get company name"""
    try:
        logger.info(f"Verifying ticker: {symbol}")
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if info:
            if 'longName' in info:
                return True, info['longName']
            elif 'shortName' in info:
                return True, info['shortName']
            return True, symbol
                
        return False, None
    except Exception as e:
        logger.error(f"Error verifying ticker {symbol}: {str(e)}")
        return False, None


def load_tickers():
    """Load tickers from TypeScript file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, '..', 'tickers.ts')
        
        logger.debug(f"Current directory: {current_dir}")
        logger.debug(f"Looking for tickers.ts at: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"Tickers file not found at: {file_path}")
            file_path = os.path.join(os.getcwd(), 'tickers.ts')
            logger.debug(f"Trying current directory: {file_path}")
            
            if not os.path.exists(file_path):
                logger.error("Tickers file not found in current directory either")
                return [], {}
        
        logger.info(f"Found tickers.ts at: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"Read {len(content)} characters from tickers.ts")
            
        pattern = r'{[^}]*symbol:\s*"([^"]*)",[^}]*name:\s*"([^"]*)"[^}]*}'
        matches = re.finditer(pattern, content)
        
        TICKERS = []
        TICKER_DICT = {}
        
        for match in matches:
            symbol, name = match.groups()
            ticker_obj = {"symbol": symbol, "name": name}
            TICKERS.append(ticker_obj)
            TICKER_DICT[symbol] = name
        
        logger.info(f"Successfully loaded {len(TICKERS)} tickers")
        logger.debug(f"First few tickers: {TICKERS[:3]}")
        
        return TICKERS, TICKER_DICT
        
    except Exception as e:
        logger.error(f"Error loading tickers: {str(e)}")
        logger.error(traceback.format_exc())
        return [], {}

# Load tickers at module level
TICKERS, TICKER_DICT = load_tickers()

@bp.route('/')
def index():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', now=datetime.now(), max_date=today)


@bp.route('/search_ticker', methods=['GET'])
def search_ticker():
    query = request.args.get('query', '').upper()
    if not query or len(query) < 1:
        return jsonify([])
    
    try:
        search_results = []
        logger.info(f"Searching for ticker: {query}")
        
        # List of variations to try
        variations = [query]
        
        # Add '^' prefix variation if not present
        if not query.startswith('^'):
            variations.append(f'^{query}')
        # If query starts with '^', also try without it
        else:
            variations.append(query[1:])
            
        logger.info(f"Trying ticker variations: {variations}")
        
        # Try each variation
        for variant in variations:
            # Check for market-specific patterns first
            exchange_suffix = None
                  
            # Shanghai Stock Exchange (.SS)
            if (variant.startswith('60') or variant.startswith('68') or 
                variant.startswith('5')) and len(variant) == 6:
                exchange_suffix = '.SS'
                
            # Shenzhen Stock Exchange (.SZ)
            elif (variant.startswith('00') or variant.startswith('3')) and len(variant) == 6:
                exchange_suffix = '.SZ'
                
            # Hong Kong Exchange (.HK)
            elif (variant.startswith('00') or 
                  variant.startswith('0')) and len(variant) == 4:
                exchange_suffix = '.HK'

            # Check with exchange suffix if applicable
            if exchange_suffix:
                symbol_to_check = f"{variant}{exchange_suffix}"
                is_valid, company_name = verify_ticker(symbol_to_check)
                
                if is_valid and symbol_to_check.upper() != company_name.upper():  # Only add if symbol and name are different
                    search_results.append({
                        'symbol': symbol_to_check,
                        'name': company_name,
                        'source': 'verified'
                    })
                    logger.info(f"Found verified stock: {symbol_to_check}")
            else:
                is_valid, company_name = verify_ticker(variant)
                if is_valid and variant.upper() != company_name.upper():  # Only add if symbol and name are different
                    search_results.append({
                        'symbol': variant,
                        'name': company_name,
                        'source': 'verified'
                    })
                    logger.info(f"Found verified stock: {variant}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for result in search_results:
            if result['symbol'] not in seen:
                seen.add(result['symbol'])
                unique_results.append(result)
        search_results = unique_results
                
        # Only proceed with local search if no verified stock was found
        if not search_results:
            # Check local dictionary for both variations
            for variant in variations:
                if variant in TICKER_DICT:
                    name = TICKER_DICT[variant]
                    if variant.upper() != name.upper():  # Only add if symbol and name are different
                        search_results.append({
                            'symbol': variant,
                            'name': name,
                            'source': 'local'
                        })
                        logger.info(f"Found local match: {variant}")
            
            # Add partial matches from local data
            if len(search_results) < 5:
                partial_matches = []
                for variant in variations:
                    matches = [
                        {'symbol': ticker['symbol'], 'name': ticker['name'], 'source': 'local'}
                        for ticker in TICKERS
                        if (variant in ticker['symbol'].upper() or 
                            variant in ticker['name'].upper()) and 
                            ticker['symbol'] not in seen and
                            ticker['symbol'].upper() != ticker['name'].upper() and  # Only add if symbol and name are different
                            not any(r['symbol'] == ticker['symbol'] for r in search_results)
                    ]
                    partial_matches.extend(matches)
                
                # Remove duplicates and add to results
                for match in partial_matches:
                    if match['symbol'] not in seen:
                        seen.add(match['symbol'])
                        search_results.append(match)
                        if len(search_results) >= 5:
                            break
                
                logger.info(f"Found {len(partial_matches)} partial matches")
            
        return jsonify(search_results[:5])
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify([])
    


@bp.route('/quick_analyze', methods=['POST'])
def quick_analyze():
    """Quick analysis route for non-logged-in users"""
    try:
        ticker_input = request.form.get('ticker', '').split()[0].upper()
        if not ticker_input:
            raise ValueError("Ticker symbol is required")
            
        # Use default values for quick analysis
        fig = create_stock_visualization(
            ticker_input,
            end_date=None,  # Use current date
            lookback_days=365,  # Default lookback
            crossover_days=365  # Default crossover
        )
        
        html_content = fig.to_html(
            full_html=True,
            include_plotlyjs=True,
            config={'responsive': True}
        )
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
        
    except Exception as e:
        error_msg = f"Error analyzing {ticker_input}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return render_template('error.html', error=error_msg), 500

@bp.route('/analyze', methods=['POST'])
@login_required  # Add login requirement for full analysis
def analyze():
    try:
        ticker_input = request.form.get('ticker', '').split()[0].upper()
        logger.info(f"Analyzing ticker: {ticker_input}")
        
        if not ticker_input:
            raise ValueError("Ticker symbol is required")
        
        end_date = request.form.get('end_date')
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
                logger.info(f"Using end date: {end_date}")
            except ValueError:
                raise ValueError("Invalid date format. Please use YYYY-MM-DD format")
        
        lookback_days = int(request.form.get('lookback_days', 365))
        if lookback_days < 30 or lookback_days > 10000:
            raise ValueError("Lookback days must be between 30 and 10000")
        
        crossover_days = int(request.form.get('crossover_days', 365))
        if crossover_days < 30 or crossover_days > 1000:
            raise ValueError("Crossover days must be between 30 and 1000")
        
        fig = create_stock_visualization(
            ticker_input,
            end_date=end_date,
            lookback_days=lookback_days,
            crossover_days=crossover_days
        )
        
        html_content = fig.to_html(
            full_html=True,
            include_plotlyjs=True,
            config={'responsive': True}
        )
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
        
    except Exception as e:
        error_msg = f"Error analyzing {ticker_input}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return render_template('error.html', error=error_msg), 500

@bp.route('/tables')
def tables():
    """Show database tables in document tree structure"""
    try:
        logger.info('Accessing database tables view')
        
        # Get all tables from database
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f'Found {len(tables)} tables in database')
        
        # Organize tables by type
        historical_tables = []
        financial_tables = []
        other_tables = []
        
        for table in tables:
            try:
                table_info = {
                    'name': table
                }
                
                if table.startswith('his_'):
                    ticker = table.replace('his_', '').upper()
                    historical_tables.append({
                        **table_info,
                        'ticker': ticker,
                        'type': 'Historical Data'
                    })
                    
                elif table.startswith('roic_'):
                    ticker = table.replace('roic_', '').upper()
                    financial_tables.append({
                        **table_info,
                        'ticker': ticker,
                        'type': 'Financial Data'
                    })
                    
                else:
                    other_tables.append({
                        **table_info,
                        'type': 'Other'
                    })
                    
            except Exception as table_error:
                logger.error(f"Error processing table {table}: {str(table_error)}")
                continue

        return render_template(
            'tables.html',
            historical_tables=historical_tables,
            financial_tables=financial_tables,
            other_tables=other_tables
        )
        
    except Exception as e:
        error_msg = f"Error fetching database tables: {str(e)}"
        logger.error(f"{error_msg}")
        return render_template('tables.html', error=error_msg)

@bp.route('/delete_table/<table_name>', methods=['POST'])
def delete_table(table_name):
    """Delete a table from database"""
    try:
        logger.info(f'Attempting to delete table: {table_name}')
        
        # Check if table exists
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            logger.error(f'Table {table_name} not found')
            return jsonify({'success': False, 'error': 'Table not found'}), 404

        # Use backticks to properly escape table name
        query = text(f'DROP TABLE `{table_name}`')
        db.session.execute(query)
        db.session.commit()
        
        logger.info(f'Successfully deleted table: {table_name}')
        return jsonify({'success': True, 'message': f'Table {table_name} deleted successfully'})
        
    except Exception as e:
        error_msg = f"Error deleting table {table_name}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500
@bp.route('/table-content/<table_name>')
def show_table_content(table_name):
    """Show the content of a specific table with sorting and pagination"""
    try:
        # Get sort parameters from URL
        sort_column = request.args.get('sort', 'Date')  # Default sort by Date
        sort_direction = request.args.get('direction', 'desc')  # Default descending
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # 50 items per page

        # Calculate offset
        offset = (page - 1) * per_page

        # Count total rows
        count_query = text(f'SELECT COUNT(*) FROM `{table_name}`')
        total_rows = db.session.execute(count_query).scalar()
        total_pages = (total_rows + per_page - 1) // per_page

        # Get all column names
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        # If sort column not in columns, use first column
        if sort_column not in columns and columns:
            sort_column = columns[0]

        # Build query with sorting and pagination
        query = text(f'''
            SELECT * FROM `{table_name}`
            ORDER BY `{sort_column}` {sort_direction}
            LIMIT :limit OFFSET :offset
        ''')
        
        # Execute query and fetch results
        result = db.session.execute(query, {'limit': per_page, 'offset': offset})
        
        # Convert results to list of dictionaries
        data = []
        for row in result:
            row_dict = {}
            for idx, col in enumerate(columns):
                row_dict[col] = row[idx]
            data.append(row_dict)
        
        return render_template(
            'table_content.html',
            table_name=table_name,
            columns=columns,
            data=data,
            current_page=page,
            total_pages=total_pages,
            per_page=per_page,
            sort_column=sort_column,
            sort_direction=sort_direction,
            total_rows=total_rows
        )
        
    except Exception as e:
        error_msg = f"Error fetching content for table {table_name}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return render_template('table_content.html', error=error_msg)


@bp.route('/export/<table_name>/<format>')
def export_table(table_name, format):
    """Export table data in CSV or Excel format"""
    try:
        # Get all data from table
        query = text(f'SELECT * FROM `{table_name}`')
        result = db.session.execute(query)
        
        # Get column names
        columns = result.keys()
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in result], columns=columns)
        
        # Create buffer for file
        buffer = io.BytesIO()
        
        if format == 'csv':
            # Export as CSV
            df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(
                buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{table_name}.csv'
            )
            
        elif format == 'excel':
            # Export as Excel
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            return send_file(
                buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{table_name}.xlsx'
            )
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        error_msg = f"Error exporting table {table_name}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({'error': error_msg}), 500