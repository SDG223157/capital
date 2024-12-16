import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go  # Add this import

# Set pandas display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))

# Constants
API_KEY = "a365bff224a6419fac064dd52e1f80d9"
BASE_URL = "https://api.roic.ai/v1/rql"

# Metrics that should include CAGR calculation
CAGR_METRICS = {
    "total revenues",
    "operating cash flow",
    "net income",
    "earnings per share"
}
metrics_to_fetch = [
        "total revenues",
        "operating cash flow",
        "net income",
        "earnings per share",
        "operating margin",
        "capital expenditures",
        "return on invested capital",
        "Diluted Weighted Avg Shares"
        ]
# Initial financial metrics dictionary
METRICS = {
    "total revenues": "is_sales_and_services_revenues",
    "operating cash flow": "cf_cash_from_oper",
    "net income": "is_net_income",
    "earnings per share": "eps",
    "operating margin": "oper_margin",
    "capital expenditures": "cf_cap_expenditures",
    "return on invested capital": "return_on_inv_capital",
    "Diluted Weighted Avg Shares": "is_sh_for_diluted_eps"
}

def add_metric(description, field_name):
    """Adds a new metric to the METRICS dictionary"""
    description = description.lower().strip()
    field_name = field_name.strip()

    if description in METRICS:
        print(f"Warning: Metric '{description}' already exists with field '{METRICS[description]}'")
        return False

    METRICS[description] = field_name
    return True

def calculate_cagr(first_value, last_value, num_years):
    """Calculate Compound Annual Growth Rate"""
    if first_value <= 0 or last_value <= 0:
        return None
    return (pow(last_value / first_value, 1 / num_years) - 1) * 100


def get_financial_data(ticker, metric_description, start_year, end_year):
    """Fetches financial data"""
    metric_field = METRICS.get(metric_description.lower())
    if not metric_field:
        print(f"Error: Unknown metric '{metric_description}'")
        return None

    query = f"get({metric_field}(fa_period_reference=range('{start_year}', '{end_year}'))) for('{ticker}')"
    url = f"{BASE_URL}?query={query}&apikey={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        df = pd.DataFrame(response.json())
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)

        years = df['fiscal_year'].astype(int)
        values = df[metric_field].astype(float)

        return pd.Series(values.values, index=years, name=metric_description)

    except Exception as e:
        print(f"Error fetching {metric_description}: {str(e)}")
        return None
def format_number(x):
    """
    Format numbers with comprehensive handling:
    - None values: return "N/A"
    - Numbers >= 1 million (or <= -1 million): display in millions with 2 decimal places
    - Numbers between -1 million and 1 million: display with comma separators and 2 decimal places
    - Negative numbers: maintain the minus sign in all formats
    """
    if pd.isna(x) or x is None:
        return "N/A"
    try:
        # Check for absolute value >= 1 million
        if abs(x) >= 1_000_000:
            # For negative numbers, ensure the minus sign is preserved
            if x < 0:
                return f"-{abs(x/1_000_000):,.2f}M"
            else:
                return f"{x/1_000_000:,.2f}M"
        else:
            # For smaller numbers, use comma separator
            return f"{x:,.2f}"
    except (TypeError, ValueError):
        return "N/A"
def calculate_growth_rates(df):
    """Calculate period-over-period growth rates for financial metrics"""
    growth_rates = {}
    
    for metric in df.index:
        values = df.loc[metric][:-1]  # Exclude CAGR column
        if len(values) > 1:
            growth_rates[metric] = []
            for i in range(1, len(values)):
                prev_val = float(values.iloc[i-1])
                curr_val = float(values.iloc[i])
                if prev_val and prev_val != 0:  # Avoid division by zero
                    growth = ((curr_val / prev_val) - 1) * 100
                    growth_rates[metric].append(growth)
                else:
                    growth_rates[metric].append(None)
    
    return growth_rates

def format_growth_values(growth_rates):
    """Format growth rates for display in table with sign handling"""
    if not growth_rates:
        return []
    
    # Get list of metrics and periods
    metrics = list(growth_rates.keys())
    if not metrics or not growth_rates[metrics[0]]:
        return []
    
    periods = len(growth_rates[metrics[0]])
    
    # Format metric names
    formatted_values = [metrics]
    
    # Format growth rates for each period
    for i in range(periods):
        period_values = []
        for metric in metrics:
            value = growth_rates[metric][i]
            if value is None:
                period_values.append("N/A")
            else:
                # Format with sign and one decimal place
                period_values.append(f"{value:+.1f}%" if value != 0 else "0.0%")
        formatted_values.append(period_values)
    
    return formatted_values
def format_large_number(x):
    """
    Format numbers:
    - Numbers >= 1 million: show in millions with 2 decimals
    - Numbers < 1 million: show with comma separators and 2 decimals
    """
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:,.0f}M"
    return f"{x:,.2f}"

def create_financial_metrics_table(df):
    """
    Creates a formatted financial metrics table for display
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing financial metrics
    
    Returns:
    tuple: (metrics_table, growth_table) - Plotly table objects
    """
    if df is None or df.empty:
        return None, None

    # Format numbers with comprehensive handling
    formatted_df = df.copy()
    for col in df.columns:
        if col != 'CAGR %':
            formatted_df[col] = formatted_df[col].apply(format_number)
        else:
            # Handle CAGR formatting with negative check and sign
            formatted_df[col] = formatted_df[col].apply(
                lambda x: f"{x:+.2f}" if pd.notna(x) and x is not None else "N/A"
            )

    # Create the metrics table
    metrics_table = go.Table(
        domain=dict(x=[0, 1], y=[0.12, 0.37]),  # Position for metrics table
        header=dict(
            values=['<b>Metric</b>'] + [f'<b>{col}</b>' for col in df.columns],
            fill_color='lightgrey',
            align='left',
            font=dict(size=12)
        ),
        cells=dict(
            values=[
                formatted_df.index.tolist(),
                *[formatted_df[col].tolist() for col in formatted_df.columns]
            ],
            align=['left'] + ['right'] * len(df.columns),  # Left align text, right align numbers
            font=dict(size=11),
            fill_color=[
                ['white'] * len(formatted_df),  # Background color for each row
                *[['white'] * len(formatted_df)] * len(df.columns)
            ]
        )
    )
    
    # Create growth rates table
    growth_table = None
    if df is not None and not df.empty:
        growth_rates = calculate_growth_rates(df)
        if growth_rates:
            formatted_values = format_growth_values(growth_rates)
            if formatted_values:
                growth_table = go.Table(
                    domain=dict(x=[0, 1], y=[0.45, 0.53]),  # Position for growth table
                    header=dict(
                        values=['<b>Metric</b>'] + [f'<b>{df.columns[i]} Growth</b>' 
                               for i in range(1, len(df.columns)-1)],
                        fill_color='lightgrey',
                        align='left',
                        font=dict(size=12)
                    ),
                    cells=dict(
                        values=formatted_values,
                        align=['left'] + ['right'] * (len(formatted_values) - 1),  # Left align text, right align numbers
                        font=dict(size=11),
                        fill_color=[
                            ['white'] * len(formatted_values[0]),  # Background color for each row
                            *[['white'] * len(formatted_values[0])] * (len(formatted_values) - 1)
                        ]
                    )
                )
    
    return metrics_table, growth_table

def create_metrics_table(ticker, metrics, start_year, end_year):
    """Creates a combined table of all metrics with selective growth rates"""
    data = {}
    growth_rates = {}

    for metric in metrics:
        metric = metric.lower()
        series = get_financial_data(ticker.upper(), metric, start_year, end_year)
        if series is not None:
            data[metric] = series

            # Calculate CAGR only for specified metrics
            if metric in CAGR_METRICS:
                first_value = series.iloc[0]
                last_value = series.iloc[-1]
                num_years = len(series) - 1
                if num_years > 0:
                    growth_rate = calculate_cagr(first_value, last_value, num_years)
                    if growth_rate is not None:
                        growth_rates[metric] = growth_rate

    if data:
        # Create main DataFrame with metrics
        df = pd.DataFrame(data).T

        # Add growth rates column only for specified metrics
        df['CAGR %'] = None  # Initialize with None
        for metric in CAGR_METRICS:
            if metric in growth_rates and metric in df.index:
                df.at[metric, 'CAGR %'] = growth_rates[metric]

        # Format the table
        table_str = df.to_string()
        table_width = len(table_str.split('\n')[0])

        print(f"\n{ticker} Financial Data ({start_year}-{end_year})")
        print("-" * table_width)
        print(table_str)
        print("-" * table_width)
        print("\nCAGR: Compound Annual Growth Rate (calculated only for selected metrics)")

        return df
    return None


    """Creates a formatted financial metrics table for display"""
    if df is None or df.empty:
        return None, None
        
    # Create the metrics table with adjusted domain
    metrics_table = go.Table(
        domain=dict(x=[0, 1], y=[0, 0.15]),  # Moved to bottom
        header=dict(
            values=['<b>Metric</b>'] + [f'<b>{col}</b>' for col in df.columns],
            fill_color='lightgrey',
            align='left',
            font=dict(size=12)
        ),
        cells=dict(
            values=[
                df.index.tolist(),
                *[df[col].tolist() for col in df.columns[:-1]],
                df['CAGR %'].tolist()
            ],
            align='left',
            font=dict(size=11),
            format=[None, *['.2f' for _ in range(len(df.columns)-1)], '.2f%']
        )
    )
    
    # Create growth rates table with adjusted domain
    growth_table = None
    if df is not None and not df.empty:
        growth_rates = calculate_growth_rates(df)  # Implement this helper function
        if growth_rates:
            growth_table = go.Table(
                domain=dict(x=[0, 1], y=[0.16, 0.25]),  # Positioned above metrics table
                header=dict(
                    values=['<b>Metric</b>'] + [f'<b>{col} Growth</b>' for col in df.columns[1:-1]],
                    fill_color='lightgrey',
                    align='left',
                    font=dict(size=12)
                ),
                cells=dict(
                    values=format_growth_values(growth_rates),  # Implement this helper function
                    align='left',
                    font=dict(size=11)
                )
            )
    
    return metrics_table, growth_table

# Now let's modify the create_combined_analysis function in analysis.py
# Add this to the imports at the top:

if __name__ == "__main__":
    # Parameters
    TICKER = "600519.ss"
    START_YEAR = "2016"
    END_YEAR = "2024"
    add_metric("net income", "is_net_income")
    add_metric("gross profit", "is_gross_profit")
    add_metric("total assets", "bs_total_assets")
    add_metric("earnings per share", "eps")
    add_metric("capital expenditures", "cf_cap_expenditures")
    add_metric("Operating Margin", "oper_margin")
    add_metric("Return on Invested Capital", "return_on_inv_capital")
    add_metric("Diluted Weighted Avg Shares", "is_sh_for_diluted_eps")

    # All metrics to fetch (CAGR will only be calculated for those in CAGR_METRICS)



    # Create and display table
    df = create_metrics_table(
        ticker=TICKER,
        metrics=metrics_to_fetch,
        start_year=START_YEAR,
        end_year=END_YEAR
    )