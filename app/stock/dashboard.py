import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
import json
import datetime

def analyze_stock_multi_period(ticker_symbol, period="5y"):
    """
    Analyzes a stock by calculating volatility based on actual daily, weekly, and monthly returns
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Get daily data
        daily_data = stock.history(period=period)
        if len(daily_data) == 0:
            return None, None, None
        
        # Calculate daily returns and volatility
        daily_data['Return'] = daily_data['Close'].pct_change()
        daily_data['Volatility'] = daily_data['Return'].rolling(window=21).std() * np.sqrt(252)
        daily_data['MA_100'] = daily_data['Close'].rolling(window=100).mean()
        daily_data['MA_200'] = daily_data['Close'].rolling(window=200).mean()
        
        # Only calculate MA_500 and MA_1000 if we have enough data
        if len(daily_data) >= 500:
            daily_data['MA_500'] = daily_data['Close'].rolling(window=500).mean()
        else:
            daily_data['MA_500'] = np.nan
            
        if len(daily_data) >= 1000:
            daily_data['MA_1000'] = daily_data['Close'].rolling(window=1000).mean()
        else:
            daily_data['MA_1000'] = np.nan
        
        # Get weekly data (actual weekly returns, not rolling)
        weekly_data = stock.history(period=period, interval="1wk")
        weekly_data['Return'] = weekly_data['Close'].pct_change()
        weekly_data['Volatility'] = weekly_data['Return'].rolling(window=4).std() * np.sqrt(52)
        
        # Get monthly data (actual monthly returns, not rolling)
        monthly_data = stock.history(period=period, interval="1mo")
        monthly_data['Return'] = monthly_data['Close'].pct_change()
        monthly_data['Volatility'] = monthly_data['Return'].rolling(window=3).std() * np.sqrt(12)
        
        return daily_data, weekly_data, monthly_data
    
    except Exception as e:
        print(f"Error analyzing {ticker_symbol}: {str(e)}")
        return None, None, None

def create_plotly_dashboard(daily_data, weekly_data, monthly_data, ticker_symbol):
    """
    Creates an interactive Plotly dashboard with price and volatility across timeframes
    """
    # Create figure with subplots
    fig = make_subplots(
        rows=3, 
        cols=2,
        shared_xaxes=False,
        vertical_spacing=0.08,
        horizontal_spacing=0.05,
        subplot_titles=(
            f"{ticker_symbol} - Daily Price & Moving Averages", f"{ticker_symbol} - Weekly & Monthly Price",
            "Daily Volatility", "Weekly & Monthly Volatility",
            "Current Metrics", "Historical Volatility Comparison"
        ),
        row_heights=[0.5, 0.25, 0.25],
        specs=[
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "table"}, {"type": "table"}]
        ]
    )
    
    # Add traces for price, volatility, and tables (implementation same as previous)
    # Implementation continues with all the chart components...
    
    # Return the figure as JSON for rendering in the template
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_stock_analysis(ticker, period):
    """
    Generate stock analysis for the given ticker and period
    """
    # Get data for the ticker and period
    daily_data, weekly_data, monthly_data = analyze_stock_multi_period(ticker, period)
    
    if daily_data is None or len(daily_data) == 0:
        return None, f"No data found for {ticker}"
    
    # Create dashboard figure
    fig_json = create_plotly_dashboard(daily_data, weekly_data, monthly_data, ticker)
    
    # Generate info text
    info = {
        "ticker": ticker,
        "period": period,
        "daily_points": len(daily_data),
        "weekly_points": len(weekly_data),
        "monthly_points": len(monthly_data),
        "start_date": daily_data.index[0].strftime('%Y-%m-%d'),
        "end_date": daily_data.index[-1].strftime('%Y-%m-%d')
    }
    
    return fig_json, info