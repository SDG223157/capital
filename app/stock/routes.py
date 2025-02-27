from flask import Blueprint, render_template, request, jsonify
from app.stock.dashboard import get_stock_analysis
import plotly.utils
import json

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

@stock_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Show the stock analysis dashboard"""
    ticker = request.args.get('ticker', 'AAPL')
    period = request.args.get('period', '2y')
    
    # Get initial data
    fig, info = get_stock_analysis(ticker, period)
    
    if fig is None:
        # Handle error case
        return render_template('stock/dashboard.html', 
                               error=info, 
                               ticker=ticker, 
                               period=period)
    
    # Convert fig to JSON for the template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('stock/dashboard.html', 
                           graph_json=graph_json,
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
    fig, info = get_stock_analysis(ticker, period)
    
    if fig is None:
        return jsonify({"error": info}), 400
    
    # Convert fig to JSON
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return jsonify({
        "graph": graph_json,
        "info": info
    })