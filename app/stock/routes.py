from flask import Blueprint, render_template, request, jsonify
from app.stock.dashboard import get_stock_analysis

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

@stock_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Show the stock analysis dashboard"""
    ticker = request.args.get('ticker', 'AAPL')
    period = request.args.get('period', '2y')
    
    # Get initial data
    fig_json, info = get_stock_analysis(ticker, period)
    
    if fig_json is None:
        # Handle error case
        return render_template('stock/dashboard.html', 
                               error=info, 
                               ticker=ticker, 
                               period=period)
    
    return render_template('stock/dashboard.html', 
                           graph_json=fig_json,
                           info=info,
                           ticker=ticker,
                           period=period)

@stock_bp.route('/analyze', methods=['POST'])
def analyze():
    """API endpoint to get analysis data"""
    data = request.json
    ticker = data.get('ticker', 'AAPL')
    period = data.get('period', '2y')
    
    # Get analysis data
    fig_json, info = get_stock_analysis(ticker, period)
    
    if fig_json is None:
        return jsonify({"error": info}), 400
    
    return jsonify({
        "graph": fig_json,
        "info": info
    })