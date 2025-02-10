import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.utils.config.layout_config import LAYOUT_CONFIG, CHART_STYLE, TABLE_STYLE
import logging

logger = logging.getLogger(__name__)


def is_stock(symbol: str) -> bool:
    """
    Determine if a ticker represents a stock or not.
    """
    symbol = symbol.upper()
    
    # Non-stock patterns
    if (symbol.startswith('^') or 
        (symbol.startswith('58') or symbol.startswith('51')) and len(symbol) == 9 or  # Indices
        symbol.endswith('=F') or           # Futures
        symbol.endswith('-USD') or         # Crypto
        symbol.endswith('=X') or           # Forex
        symbol in ['USD', 'EUR', 'GBP', 'JPY', 'CNH', 'HKD', 'CAD', 'AUD'] or  # Major currencies
        any(suffix in symbol for suffix in ['-P', '-C', '-IV', '-UV'])):  # Options, ETF variations
        return False
    
    return True

class VisualizationService:
    """Service class for creating and managing stock analysis visualizations."""

    @staticmethod
    def _get_config(symbol: str):
        """Get the appropriate configuration based on symbol type"""
        layout_type = 'stock' if is_stock(symbol) else 'non_stock'
        return {
            'layout': layout_type,
            'chart_area': LAYOUT_CONFIG['chart_area'][layout_type],
            'tables': LAYOUT_CONFIG['tables'][layout_type],
            'annotations': LAYOUT_CONFIG['annotations'][layout_type],
            'table_style': TABLE_STYLE[layout_type]
        }

    @staticmethod
    def format_number(x):
        """Format numbers with comprehensive handling"""
        if pd.isna(x) or x is None:
            return "N/A"
        try:
            if abs(x) >= 1_000_000:
                return f"-{abs(x/1_000_000):,.0f}M" if x < 0 else f"{x/1_000_000:,.0f}M"
            else:
                return f"{x:,.2f}"
        except (TypeError, ValueError):
            return "N/A"

    @staticmethod
    def create_financial_metrics_table(df, config):
        """Create financial metrics tables using provided configuration"""
        if df is None or df.empty or config['layout'] == 'non_stock':
            return None, None

        formatted_df = df.copy()
        for col in df.columns:
            if col != 'CAGR %':
                formatted_df[col] = formatted_df[col].apply(VisualizationService.format_number)
            else:
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) and x is not None else "N/A"
                )

        metrics_table = go.Table(
            domain=dict(
                x=config['tables']['metrics']['x'],
                y=config['tables']['metrics']['y']
            ),
            header=dict(
                values=['<b>Metric</b>'] + [f'<b>{col}</b>' for col in df.columns],
                **config['table_style']['header']
            ),
            cells=dict(
                values=[
                    formatted_df.index.tolist(),
                    *[formatted_df[col].tolist() for col in formatted_df.columns]
                ],
                **config['table_style']['cells']
            )
        )
        
        growth_table = None
        if not df.empty:
            df_columns = list(df.columns)
            # Get all year columns excluding CAGR
            year_columns = [col for col in df_columns if col != 'CAGR %']
            
            # Calculate growth rates with null checking
            growth_rates = {}
            for metric in df.index:
                rates = []
                for i in range(len(year_columns)-1):
                    curr_col = year_columns[i+1]
                    prev_col = year_columns[i]
                    try:
                        curr_val = df.loc[metric, curr_col]
                        prev_val = df.loc[metric, prev_col]
                        
                        if pd.isna(curr_val) or pd.isna(prev_val) or prev_val == 0:
                            rates.append(None)
                        else:
                            growth_rate = ((curr_val / prev_val) - 1) * 100
                            rates.append(growth_rate)
                    except (TypeError, ZeroDivisionError):
                        rates.append(None)
                
                growth_rates[metric] = rates

            if growth_rates:
                # Format growth rates
                formatted_values = [list(growth_rates.keys())]  # First row is metric names
                growth_years = year_columns[1:]  # Years for growth rates (exclude first year)
                
                # Add the formatted growth rates
                for i in range(len(growth_years)):
                    period_values = []
                    for metric in growth_rates:
                        value = growth_rates[metric][i]
                        if value is None:
                            period_values.append("N/A")
                        else:
                            period_values.append(f"{value:+.1f}%" if value != 0 else "0.0%")
                    formatted_values.append(period_values)
                
                # Create the growth table
                growth_table = go.Table(
                    domain=dict(
                        x=config['tables']['growth']['x'],
                        y=config['tables']['growth']['y']
                    ),
                    header=dict(
                        values=['<b>Metric</b>'] + [f'<b>{year}</b>' for year in growth_years],
                        **config['table_style']['header']
                    ),
                    cells=dict(
                        values=formatted_values,
                        **config['table_style']['cells']
                    )
                )
        
        return metrics_table, growth_table

    @staticmethod
    def _analyze_signals(signal_returns):
        """Analyze trading signals and calculate performance metrics"""
        try:
            if not signal_returns:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'average_return': 0
                }

            trades = []
            for signal in signal_returns:
                if 'Trade Return' in signal:
                    trades.append(signal['Trade Return'])

            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'average_return': 0
                }

            winning_trades = len([t for t in trades if t > 0])
            
            return {
                'total_trades': len(trades),
                'win_rate': (winning_trades / len(trades)) * 100 if trades else 0,
                'average_return': sum(trades) / len(trades) if trades else 0
            }
        except Exception as e:
            print(f"Error analyzing signals: {str(e)}")
            return {
                'total_trades': 0,
                'win_rate': 0,
                'average_return': 0
            }

    @staticmethod
    def _get_score_stars(score):
        """Get star rating based on score value"""
        if 85 <= score <= 100:
            return "★★★★★"
        elif 75 < score < 85:
            return "★★★★"
        elif 60 <= score <= 75:
            return "★★★"
        elif 40 <= score < 60:
            return "★★"
        else:
            return "★"

    @staticmethod
    def _create_analysis_summary_table(days, end_price, annual_return, 
                                     daily_volatility, annualized_volatility,
                                     r2, regression_formula, final_score,
                                     table_style, table_domain, signal_returns=None):
        """Create the analysis summary table with colored formula and R²"""
        signal_metrics = VisualizationService._analyze_signals(signal_returns)
        stars = VisualizationService._get_score_stars(final_score)
        score_display = f"{final_score:.1f} ({stars})"
        
        try:
            equation_parts = regression_formula.split('=')
            if len(equation_parts) > 1:
                right_side = equation_parts[1].strip()
                import re
                match = re.search(r'[-+]?\d*\.?\d+', right_side)
                if match:
                    first_number = match.group()
                    formula_color = 'red' if first_number.startswith('-') else 'green'
                else:
                    formula_color = 'green'
            else:
                formula_color = 'green'
        except:
            formula_color = 'green'
            
        r2_color = 'green' if r2 > 0.7 else 'black'
        
        return go.Table(
            domain=dict(
                x=table_domain['x'],
                y=table_domain['y']
            ),
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                **table_style['header']
            ),
            cells=dict(
                values=[
                    ["Score", 'Regression Formula', 'Regression R²', 'Current Price', 
                     'Annualized Return', 'Annual Volatility', 'Total Trades',
                     'Win Rate', 'Average Trade Return'],
                    [
                        score_display,
                        regression_formula,
                        f"{r2:.4f}",
                        f"${end_price:.2f}",
                        f"{annual_return:.2f}%",
                        f"{annualized_volatility:.3f}",
                        f"{signal_metrics['total_trades']}",
                        f"{signal_metrics['win_rate']:.1f}%",
                        f"{signal_metrics['average_return']:.2f}%"
                    ]
                ],
                font=dict(
                    color=[
                        ['black'] * 9,
                        ['black', formula_color, r2_color, 'black', 'black', 'black',
                         'black', 'black', 'black']
                    ]
                ),
                **{k: v for k, v in table_style['cells'].items() if k != 'font'}
            )
        )

    
    @staticmethod
    def _create_trading_signal_table(signal_returns, table_style, table_domain):
        """Create the trading signal analysis table"""
        # Check if there are any signals with either entry or exit information
        if not signal_returns and not any('Exit Date' in signal for signal in signal_returns):
            return go.Table(
                domain=dict(
                    x=table_domain['x'],
                    y=table_domain['y']
                ),
                header=dict(
                    values=['<b>Notice</b>'],
                    **table_style['header']
                ),
                cells=dict(
                    values=[['No trading signals found in the analysis period']],
                    **table_style['cells']
                )
            )

        trades = []
        buy_signal = None
        for signal in signal_returns:
            if signal['Signal'] == 'Buy':
                buy_signal = signal
                if signal['Status'] == 'Open' and 'Trade Return' in signal:
                    trades.append({
                        'Entry Date': signal['Entry Date'].strftime('%Y-%m-%d'),
                        'Entry Price': signal['Entry Price'],
                        'Exit Date': 'Open',
                        'Exit Price': signal['Current Price'],
                        'Return': signal['Trade Return'],
                        'Status': 'Open'
                    })
            elif signal['Signal'] == 'Sell':
                if buy_signal is not None:
                    trades.append({
                        'Entry Date': buy_signal['Entry Date'].strftime('%Y-%m-%d'),
                        'Entry Price': buy_signal['Entry Price'],
                        'Exit Date': signal['Entry Date'].strftime('%Y-%m-%d'),
                        'Exit Price': signal['Entry Price'],
                        'Return': signal['Trade Return'],
                        'Status': 'Closed'
                    })
                    buy_signal = None
                elif 'Entry Date' not in signal and 'Exit Date' in signal:
                    # Handle case where we only have exit information
                    trades.append({
                        'Entry Date': 'Unknown',
                        'Entry Price': 'Unknown',
                        'Exit Date': signal['Exit Date'].strftime('%Y-%m-%d'),
                        'Exit Price': signal['Exit Price'],
                        'Return': signal.get('Trade Return', 'N/A'),
                        'Status': 'Exit Only'
                    })

        return go.Table(
            domain=dict(
                x=table_domain['x'],
                y=table_domain['y']
            ),
            header=dict(
                values=['<b>Entry Date</b>', '<b>Entry Price</b>', '<b>Exit Date</b>', 
                    '<b>Exit Price</b>', '<b>Return</b>', '<b>Status</b>'],
                **table_style['header']
            ),
            cells=dict(
                values=[
                    [t['Entry Date'] for t in trades],
                    [f"${t['Entry Price']:.2f}" if t['Entry Price'] != 'Unknown' else t['Entry Price'] for t in trades],
                    [t['Exit Date'] for t in trades],
                    [f"${t['Exit Price']:.2f}" if isinstance(t['Exit Price'], (int, float)) else t['Exit Price'] for t in trades],
                    [f"{t['Return']:.2f}%" if isinstance(t['Return'], (int, float)) else t['Return'] for t in trades],
                    [t['Status'] for t in trades]
                ],
                **table_style['cells']
            )
        )
        
    @staticmethod
    def _create_chart_annotations(config, metrics_df=None):
        """Create chart annotations"""
        annotations = []
        
        # Add table headers based on layout type
        table_headers = {
            'analysis_summary': ('Analysis Summary', True),
            'trading_signals': ('Trading Signal Analysis', True)
        }
        
        if config['layout'] == 'stock' and metrics_df is not None:
            table_headers.update({
                'metrics': ('Financial Metrics', True),
                'growth': ('Growth Analysis', True)
            })

        # Get header positions based on layout type
        layout_type = config['layout']  # 'stock' or 'non_stock'
        headers_config = config['annotations'].get('headers', {})

        # Add headers if they are in config and should be shown
        for section, (title, should_show) in table_headers.items():
            if should_show and section in headers_config:
                header_pos = headers_config[section]
                annotations.append(dict(
                    x=header_pos['x'],
                    y=header_pos['y'],
                    xref='paper',
                    yref='paper',
                    text=f'<b>{title}</b>',
                    showarrow=False,
                    font=dict(size=12),
                    align='left'
                ))

        return annotations

    @staticmethod
    def create_stock_analysis_chart(symbol, data, analysis_dates, ratios, prices, 
                                  appreciation_pcts, regression_results, 
                                  crossover_data, signal_returns, 
                                  metrics_df, total_height=LAYOUT_CONFIG['total_height']):
        """Create the complete stock analysis chart with all components"""
        config = VisualizationService._get_config(symbol)
        
        # Adjust total height for non-stocks
        if config['layout'] == 'non_stock':
            total_height *= 0.7

        fig = go.Figure()

        # Add price line
        fig.add_trace(
            go.Scatter(
                x=analysis_dates,
                y=prices,
                name='Price (Log Scale)',
                line=dict(
                    color=CHART_STYLE['colors']['price_line'],
                    **CHART_STYLE['line_styles']['price']
                ),
                yaxis='y2',
                hovertemplate='<b>Date</b>: %{x}<br>' +
                             '<b>Price</b>: $%{y:.2f}<extra></extra>'
            )
        )
        
        # Add regression components
        future_dates = pd.date_range(
            start=data.index[0],
            periods=len(regression_results['predictions']),
            freq='D'
        )
        
        fig.add_trace(
            go.Scatter(
                x=future_dates,
                y=regression_results['predictions'],
                name='Regression',
                line=dict(
                    color=CHART_STYLE['colors']['regression_line'],
                    **CHART_STYLE['line_styles']['regression']
                ),
                yaxis='y2',
                hovertemplate='<b>Date</b>: %{x}<br>' +
                             '<b>Predicted</b>: $%{y:.2f}<extra></extra>'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=future_dates,
                y=regression_results['upper_band'],
                name='Upper Band',
                line=dict(
                    color=CHART_STYLE['colors']['confidence_band'],
                    **CHART_STYLE['line_styles']['bands']
                ),
                yaxis='y2',
                showlegend=False,
                hovertemplate='<b>Date</b>: %{x}<br>' +
                             '<b>Upper Band</b>: $%{y:.2f}<extra></extra>'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=future_dates,
                y=regression_results['lower_band'],
                name='Lower Band',
                fill='tonexty',
                fillcolor='rgba(173, 216, 230, 0.2)',
                line=dict(
                    color=CHART_STYLE['colors']['confidence_band'],
                    **CHART_STYLE['line_styles']['bands']
                ),
                yaxis='y2',
                showlegend=False,
                hovertemplate='<b>Date</b>: %{x}<br>' +
                             '<b>Lower Band</b>: $%{y:.2f}<extra></extra>'
            )
        )
        
        # Add technical indicators
        fig.add_trace(
            go.Scatter(
                x=analysis_dates,
                y=ratios,
                name='Retracement Ratio',
                line=dict(
                    color=CHART_STYLE['colors']['retracement_line'],
                    **CHART_STYLE['line_styles']['retracement']
                ),
                hovertemplate='<b>Date</b>: %{x}<br>' +
                             '<b>Ratio</b>: %{y:.1f}%<extra></extra>'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=analysis_dates,
                y=appreciation_pcts,
                name='Price Position',
                line=dict(
                    color=CHART_STYLE['colors']['position_line'],
                    **CHART_STYLE['line_styles']['position']
                ),
                hovertemplate='<b>Date</b>: %{x}<br>' +
                             '<b>Position</b>: %{y:.1f}%<extra></extra>'
            )
        )
        # Add R-square line (add this code in create_stock_analysis_chart method)
        # Place this after other line traces but before crossover points
        # Add R-square line
        # Add R-square line first with detailed debugging
        # Add R-square line first with detailed logging
        # Add R-square line with contrasting color
        if 'R2_Pct' in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=analysis_dates,
                    y=data['R2_Pct'].values,
                    name='R² Quality',
                    line=dict(
                        color='#FF1493',  # Deep pink for high contrast
                        dash='dot',
                        width=2
                    ),
                    hovertemplate='<b>Date</b>: %{x}<br>' +
                                '<b>R²</b>: %{y:.1f}%<extra></extra>'
                )
            )
        # Add price line


        # Add crossover points
        if crossover_data[0]:
            dates, values, directions, prices = crossover_data
            for date, value, direction, price in zip(dates, values, directions, prices):
                color = CHART_STYLE['colors']['bullish_marker'] if direction == 'up' else CHART_STYLE['colors']['bearish_marker']
                formatted_date = date.strftime('%Y-%m-%d')
                base_name = 'Bullish Crossover' if direction == 'up' else 'Bearish Crossover'
                detailed_name = f"({formatted_date}, ${price:.2f})"
                
                fig.add_trace(
                    go.Scatter(
                        x=[date],
                        y=[value],
                        mode='markers',
                        showlegend=False,
                        name=detailed_name,
                        marker=dict(
                            color=color,
                            **CHART_STYLE['marker_styles']['crossover']
                        ),
                        hovertemplate='<b>%{text}</b><br>' +
                                     '<b>Date</b>: %{x}<br>' +
                                     '<b>Value</b>: %{y:.1f}%<br>' +
                                     '<b>Price</b>: $%{customdata:.2f}<extra></extra>',
                        text=[detailed_name],
                        customdata=[price]
                    )
                )
         # Add horizontal lines at key levels
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.1)
        fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.1)
        fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.1)
        fig.add_hline(y=80, line_dash="dash", line_color='green', opacity=0.1)

        # Add metrics tables
        metrics_table = None
        growth_table = None
        
        if config['layout'] == 'stock':
            metrics_table, growth_table = VisualizationService.create_financial_metrics_table(metrics_df, config)
            if metrics_table:
                fig.add_trace(metrics_table)
            if growth_table:
                fig.add_trace(growth_table)

        # Add analysis summary and trading signals tables
        analysis_table = VisualizationService._create_analysis_summary_table(
            days=(data.index[-1] - data.index[0]).days,
            end_price=data['Close'].iloc[-1],
            annual_return=((data['Close'].iloc[-1] / data['Close'].iloc[0]) ** (365 / (data.index[-1] - data.index[0]).days) - 1) * 100,
            daily_volatility=data['Close'].pct_change().std(),
            annualized_volatility=data['Close'].pct_change().std() * np.sqrt(252),
            r2=regression_results['r2'],
            regression_formula=regression_results['equation'],
            final_score=regression_results['total_score']['score'],
            table_style=config['table_style'],
            table_domain=config['tables']['analysis_summary'],
            signal_returns=signal_returns
        )
        fig.add_trace(analysis_table)

        trading_table = VisualizationService._create_trading_signal_table(
            signal_returns,
            table_style=config['table_style'],
            table_domain=config['tables']['trading_signals']
        )
        fig.add_trace(trading_table)

        # Create and add annotations
        annotations = VisualizationService._create_chart_annotations(config, metrics_df)

        # Update layout
        fig.update_layout(
            title=dict(
                text=f'{symbol} Analysis Snapshot',
                x=0.5,
                xanchor='center',
                y=0.95,
                yanchor='top',
                font=dict(size=30)
            ),
            height=total_height,
            showlegend=True,
            hovermode='x unified',
            annotations=annotations,
            xaxis=dict(
                title="Date",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showspikes=True,
                spikesnap='cursor',
                spikemode='across',
                spikethickness=1,
                domain=config['chart_area']['domain']['x']
            ),
            yaxis=dict(
                title="Ratio and Position (%)",
                ticksuffix="%",
                range=[-10 , 120],
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showspikes=True,
                spikesnap='cursor',
                spikemode='across',
                spikethickness=1,
                domain=config['chart_area']['domain']['y']
            ),
            yaxis2=dict(
                title="Price (Log Scale)",
                overlaying="y",
                side="right",
                type="log",
                showgrid=False,
                showspikes=True,
                spikesnap='cursor',
                spikemode='across',
                spikethickness=1,
                domain=config['chart_area']['domain']['y']
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(
            l=50,
            r=100,
            t=0.05 * total_height,
            b=0.05 * total_height,
            # Add extra right margin for legend
            autoexpand=True
        ),
        legend=dict(
            yanchor="top",
            y=0.85,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1,
            font=dict(size=11)
            )
        )

        return fig

    @staticmethod
    def print_signal_analysis(signals_df):
        """Print detailed analysis of trading signals with statistics"""
        if signals_df.empty:
            print("No trading signals found in the analysis period.")
            return
            
        print("\nTrading Signal Analysis:")
        print("-" * 50)
        
        trades = []
        buy_signal = None
        
        for _, row in signals_df.iterrows():
            if row['Signal'] == 'Buy':
                buy_signal = row
                if row['Status'] == 'Open' and 'Trade Return' in row:
                    trades.append({
                        'Buy Date': row['Entry Date'],
                        'Buy Price': row['Entry Price'],
                        'Sell Date': 'Open',
                        'Sell Price': row['Current Price'],
                        'Return': row['Trade Return'],
                        'Status': 'Open'
                    })
            elif row['Signal'] == 'Sell' and buy_signal is not None:
                trades.append({
                    'Buy Date': buy_signal['Entry Date'],
                    'Buy Price': buy_signal['Entry Price'],
                    'Sell Date': row['Entry Date'],
                    'Sell Price': row['Entry Price'],
                    'Return': row['Trade Return'],
                    'Status': 'Closed'
                })
                buy_signal = None
        
        for i, trade in enumerate(trades, 1):
            print(f"\nTrade {i}:")
            print(f"Buy:  {trade['Buy Date'].strftime('%Y-%m-%d')} at ${trade['Buy Price']:.2f}")
            if trade['Status'] == 'Open':
                print(f"Current Position: OPEN at ${trade['Sell Price']:.2f}")
            else:
                print(f"Sell: {trade['Sell Date'].strftime('%Y-%m-%d')} at ${trade['Sell Price']:.2f}")
            print(f"Return: {trade['Return']:.2f}%")
            print(f"Status: {trade['Status']}")
        
        if trades:
            returns = [trade['Return'] for trade in trades]
            closed_trades = [t for t in trades if t['Status'] == 'Closed']
            open_trades = [t for t in trades if t['Status'] == 'Open']
            
            print("\nSummary Statistics:")
            print("-" * 50)
            print(f"Total Trades: {len(trades)}")
            print(f"Closed Trades: {len(closed_trades)}")
            print(f"Open Trades: {len(open_trades)}")
            if returns:
                print(f"Average Return per Trade: {np.mean(returns):.2f}%")
                print(f"Best Trade: {max(returns):.2f}%")
                print(f"Worst Trade: {min(returns):.2f}%")
                print(f"Win Rate: {len([r for r in returns if r > 0]) / len(returns) * 100:.1f}%")
            else:
                print("No completed trades to calculate statistics.")