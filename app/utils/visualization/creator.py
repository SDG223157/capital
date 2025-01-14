# src/visualization/creator.py
import pandas as pd
from datetime import datetime
from app.utils.config.metrics_config import METRICS_TO_FETCH, ANALYSIS_DEFAULTS
from app.utils.config.api_config import ROIC_API
from app.utils.data.data_service import DataService
from app.utils.analysis.analysis_service import AnalysisService
from app.utils.visualization.visualization_service import VisualizationService
from typing import Optional



def create_stock_visualization(
    ticker: str, 
    end_date: Optional[str] = None, 
    lookback_days: int = ANALYSIS_DEFAULTS['lookback_days'],
    crossover_days: int = ANALYSIS_DEFAULTS['crossover_days']
) -> 'plotly.graph_objects.Figure':
    """
    Create a complete stock analysis visualization
    """
    analysis_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    print(f"Starting analysis {analysis_id} for {ticker}")
    try:
        # Initialize services
        data_service = DataService()
        
        # Set up dates
        if end_date is None or not end_date.strip():
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate extended start date for ratio calculations
        extended_lookback = lookback_days + crossover_days
        extended_start_date = data_service.get_analysis_dates(end_date, 'days', extended_lookback)
        display_start_date = data_service.get_analysis_dates(end_date, 'days', lookback_days)
        
        print(f"Fetching extended historical data for {ticker} from {extended_start_date} to {end_date}")
        
        # Get extended historical data for calculations
        historical_data_extended = data_service.get_historical_data(ticker, extended_start_date, end_date)
        
        if historical_data_extended.empty:
            raise ValueError(f"No historical data found for {ticker}")
        
        print("Performing technical analysis...")
        # Perform technical analysis on extended data
        analysis_df = AnalysisService.analyze_stock_data(historical_data_extended, crossover_days)
        
        # Debug prints for DataFrame structure
        print("Analysis DataFrame structure:")
        print("Columns:", analysis_df.columns.tolist())
        print("Index:", type(analysis_df.index))
        
        # Filter data for display period using index
        display_start = pd.to_datetime(display_start_date)
        historical_data = historical_data_extended[historical_data_extended.index >= display_start]
        # This is the line that was causing the error - replaced with index filtering
        analysis_df = analysis_df[analysis_df.index >= display_start]
        
        print("Filtered analysis DataFrame rows:", len(analysis_df))
        
        # Perform regression analysis on display period data
        regression_results = AnalysisService.perform_polynomial_regression(
            historical_data, 
            future_days=int(lookback_days*LAYOUT_CONFIG['lookback_days_ratio'])
        )
        
        # Find crossover points within display period using index
        crossover_data = AnalysisService.find_crossover_points(
            analysis_df.index.tolist(),
            analysis_df['Retracement_Ratio_Pct'].tolist(),
            analysis_df['Price_Position_Pct'].tolist(),
            analysis_df['Price'].tolist()
        )
        
        print("Fetching financial metrics...")
        # Get financial metrics
        current_year = datetime.now().year
        metrics_df = data_service.create_metrics_table(
            ticker=ticker,
            metrics=METRICS_TO_FETCH,
            start_year=str(current_year - 10),
            end_year=str(current_year)
        )
        
        # Prepare signal returns data
        print("Analyzing trading signals...")
        signal_returns = []
        if crossover_data[0]:  # If there are crossover points
            dates, values, directions, prices = crossover_data
            current_position = None
            entry_price = None
            
            for date, value, direction, price in zip(dates, values, directions, prices):
                if direction == 'up' and current_position is None:  # Buy signal
                    entry_price = price
                    current_position = 'long'
                    signal_returns.append({
                        'Entry Date': date,
                        'Entry Price': price,
                        'Signal': 'Buy',
                        'Status': 'Open'
                    })
                elif direction == 'down' and current_position == 'long':  # Sell signal
                    exit_price = price
                    trade_return = ((exit_price / entry_price) - 1) * 100
                    current_position = None
                    
                    if signal_returns:
                        signal_returns[-1]['Status'] = 'Closed'
                    
                    signal_returns.append({
                        'Entry Date': date,
                        'Entry Price': price,
                        'Signal': 'Sell',
                        'Trade Return': trade_return,
                        'Status': 'Closed'
                    })
            
            # Handle open position
            if current_position == 'long':
                last_price = historical_data['Close'].iloc[-1]
                open_trade_return = ((last_price / entry_price) - 1) * 100
                if signal_returns and signal_returns[-1]['Signal'] == 'Buy':
                    signal_returns[-1]['Trade Return'] = open_trade_return
                    signal_returns[-1]['Current Price'] = last_price
        
        print("Creating visualization...")
        # Check if R2_Pct exists in the DataFrame
        if 'R2_Pct' in analysis_df.columns:
            print("R2_Pct column found with values:", analysis_df['R2_Pct'].head())
        else:
            print("R2_Pct column not found in DataFrame")
        
        # Create visualization
        fig = VisualizationService.create_stock_analysis_chart(
            symbol=ticker,
            data=analysis_df,
            analysis_dates=analysis_df.index.tolist(),
            ratios=analysis_df['Retracement_Ratio_Pct'].tolist(),
            prices=analysis_df['Price'].tolist(),
            appreciation_pcts=analysis_df['Price_Position_Pct'].tolist(),
            regression_results=regression_results,
            crossover_data=crossover_data,
            signal_returns=signal_returns,
            metrics_df=metrics_df
        )
        
        print("Analysis completed successfully!")
        return fig
    
    except Exception as e:
        print(f"Error in create_stock_visualization: {str(e)}")
        raise

def save_visualization(fig, ticker: str, output_dir: str = "outputs") -> dict:
    """
    Save visualization in multiple formats

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        The visualization figure to save
    ticker : str
        Stock ticker symbol for filename
    output_dir : str
        Directory to save outputs

    Returns
    -------
    dict
        Dictionary containing paths to saved files
    """
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate base filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"{ticker}_analysis_{timestamp}"
    
    saved_files = {}
    
    try:
        # Save as interactive HTML
        html_path = os.path.join(output_dir, f"{base_filename}.html")
        fig.write_html(
            html_path,
            include_plotlyjs=True,
            full_html=True,
            auto_open=True
        )
        saved_files['html'] = html_path
        print(f"Interactive HTML saved to: {html_path}")
        
        try:
            # Save as static image (PNG)
            png_path = os.path.join(output_dir, f"{base_filename}.png")
            fig.write_image(
                png_path,
                width=1920,
                height=1080,
                scale=2
            )
            saved_files['png'] = png_path
            print(f"Static PNG saved to: {png_path}")
            
            # Save as PDF
            pdf_path = os.path.join(output_dir, f"{base_filename}.pdf")
            fig.write_image(
                pdf_path,
                width=1920,
                height=1080
            )
            saved_files['pdf'] = pdf_path
            print(f"PDF saved to: {pdf_path}")
            
        except Exception as e:
            print(f"Warning: Could not save static images. Error: {str(e)}")
            print("You may need to install additional dependencies:")
            print("pip install -U kaleido")
    
    except Exception as e:
        print(f"Error saving visualization: {str(e)}")
        raise
    
    return saved_files