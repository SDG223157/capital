import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Union

class PolynomialTradingSystem:
    """Trading system based on polynomial regression pattern analysis"""
    def __init__(self, 
                 data: pd.DataFrame,
                 period_years: float = 2,
                 max_position_size: float = 0.25,
                 min_rsquared: float = 0.85):
        self.data = data
        self.period_years = period_years
        self.trading_days = int(252 * period_years)
        self.max_position_size = max_position_size
        self.min_rsquared = min_rsquared
        
        # Calculate basic metrics
        self.calculate_regression()
        self.calculate_volatility()
        
    def calculate_regression(self):
        """Calculate polynomial regression coefficients"""
        try:
            # Prepare data
            log_prices = np.log(self.data['Close'].values)
            x = np.arange(len(log_prices)).reshape(-1, 1)
            x_scaled = x / len(x)
            
            # Fit polynomial regression
            X = np.column_stack([x_scaled**2, x_scaled, np.ones_like(x_scaled)])
            coeffs = np.linalg.lstsq(X, log_prices, rcond=None)[0]
            
            self.quad_coef = coeffs[0]
            self.linear_coef = coeffs[1]
            self.constant = coeffs[2]
            
            # Calculate R-squared
            y_pred = X @ coeffs
            ss_tot = np.sum((log_prices - np.mean(log_prices))**2)
            ss_res = np.sum((log_prices - y_pred)**2)
            self.r_squared = 1 - ss_res/ss_tot
            
        except Exception as e:
            raise Exception(f"Error in regression calculation: {str(e)}")
    
    def calculate_volatility(self):
        """Calculate volatility metrics"""
        returns = np.diff(np.log(self.data['Close'].values))
        self.daily_volatility = np.std(returns)
        self.annual_volatility = self.daily_volatility * np.sqrt(252)
        
    def calculate_growth_rate(self, x: int) -> Tuple[float, float]:
        """Calculate growth rate at point x"""
        x_norm = x / len(self.data)
        
        # Calculate daily rate
        daily_rate = (
            2 * self.quad_coef * x_norm / len(self.data) +
            self.linear_coef / len(self.data)
        )
        
        # Convert to annual
        annual_rate = daily_rate * 252
        
        return daily_rate, annual_rate
    
    def calculate_log_price(self, x: int) -> float:
        """Calculate log price at point x"""
        x_norm = x / len(self.data)
        return (
            self.quad_coef * x_norm**2 +
            self.linear_coef * x_norm +
            self.constant
        )
    
    def get_trading_signals(self, 
                          x: int,
                          price: float,
                          growth_rate: float) -> Dict[str, Union[str, float]]:
        """Generate trading signals based on growth rate"""
        # Define growth rate zones (ordered from highest to lowest rate)
        zones = {
            'Extreme_Bull': {'rate': 25, 'action': 'Strong Sell'},
            'Bull': {'rate': 15, 'action': 'Trim'},
            'Neutral': {'rate': 5, 'action': 'Hold'},
            'Bear': {'rate': -5, 'action': 'Buy'},
            'Extreme_Bear': {'rate': -15, 'action': 'Strong Buy'}
        }
        
        # Calculate annual rate
        annual_rate = growth_rate * 252 * 100
        
        # Find appropriate zone (fixed version)
        current_zone = 'Extreme_Bear'  # Default to most bearish
        for zone, info in zones.items():
            if annual_rate > info['rate']:
                current_zone = zone
                break
        
        # Calculate position size based on zone
        position_size = 0
        if current_zone == 'Extreme_Bear':
            position_size = self.max_position_size
        elif current_zone == 'Bear':
            position_size = 0.75 * self.max_position_size
        elif current_zone == 'Neutral':
            position_size = 0.5 * self.max_position_size
        elif current_zone == 'Bull':
            position_size = 0.25 * self.max_position_size
        
        # Calculate stops
        technical_stop = price * (1 - 2 * self.daily_volatility)
        growth_stop = price * (1 - abs(annual_rate/100))
        stop_loss = max(technical_stop, growth_stop)
        
        # Calculate targets
        target1 = price * (1 + abs(annual_rate/100))
        target2 = price * (1 + 1.5 * abs(annual_rate/100))
        target3 = price * (1 + 2 * abs(annual_rate/100))
        
        return {
            'zone': current_zone,
            'action': zones[current_zone]['action'],
            'position_size': position_size,
            'stop_loss': stop_loss,
            'targets': [target1, target2, target3],
            'growth_rate': annual_rate
        }

class BacktestAnalyzer:
    """Backtesting system for polynomial trading strategy"""
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.trades = []
        
    def run_backtest(self, system, data):
        """Run backtest with position tracking"""
        capital = self.initial_capital
        position = 0
        entry_price = 0
        entry_date = None
        trade_id = 0
        unrealized_pnl = 0
        current_stop = 0
        current_targets = []
        
        daily_stats = []
        
        for i in range(len(data)):
            date = data.index[i]
            price = data['Close'].iloc[i]
            
            # Get current signals
            daily_rate, annual_rate = system.calculate_growth_rate(i)
            signals = system.get_trading_signals(i, price, daily_rate)
            
            # Track daily position
            if position > 0:
                unrealized_pnl = position * capital * (price/entry_price - 1)
            
            # Position Management
            trade_action = None
            trade_shares = 0
            
            if position == 0:  # No position
                if signals['action'] in ['Strong Buy', 'Buy'] and system.r_squared >= system.min_rsquared:
                    position = signals['position_size']
                    entry_price = price
                    entry_date = date
                    trade_id += 1
                    current_stop = signals['stop_loss']
                    current_targets = signals['targets']
                    trade_shares = (capital * position) / price
                    trade_action = 'ENTRY'
                    
            elif position > 0:  # Managing existing position
                # Check stops
                if price <= current_stop:
                    trade_action = 'STOP'
                    trade_shares = -(capital * position) / entry_price
                    position = 0
                    
                # Check targets
                elif price >= current_targets[2]:
                    trade_action = 'TARGET_3'
                    trade_shares = -(capital * position) / entry_price
                    position = 0
                elif price >= current_targets[1] and position > 0.5:
                    trade_action = 'TARGET_2'
                    trade_shares = -(capital * position * 0.5) / entry_price
                    position *= 0.5
                elif price >= current_targets[0] and position > 0.75:
                    trade_action = 'TARGET_1'
                    trade_shares = -(capital * position * 0.25) / entry_price
                    position *= 0.75
                    
                # Check signals for exits
                elif signals['action'] in ['Strong Sell', 'Trim']:
                    exit_size = min(position, 1 - signals['position_size'])
                    if exit_size > 0:
                        trade_action = 'SIGNAL_EXIT'
                        trade_shares = -(capital * exit_size) / entry_price
                        position -= exit_size
            
            # Record trade if any action taken
            if trade_action:
                trade = {
                    'trade_id': trade_id,
                    'date': date,
                    'action': trade_action,
                    'price': price,
                    'shares': trade_shares,
                    'value': abs(trade_shares * price),
                    'entry_price': entry_price if trade_action == 'ENTRY' else None,
                    'stop_loss': current_stop if trade_action == 'ENTRY' else None,
                    'targets': current_targets if trade_action == 'ENTRY' else None,
                    'pnl': -trade_shares * (price - entry_price) if trade_action != 'ENTRY' else 0
                }
                self.trades.append(trade)
            
            # Record daily statistics
            daily_stat = {
                'date': date,
                'price': price,
                'position': position,
                'capital': capital + unrealized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'growth_rate': annual_rate,
                'signal': signals['action'],
                'zone': signals['zone']
            }
            daily_stats.append(daily_stat)
        
        return pd.DataFrame(daily_stats), pd.DataFrame(self.trades)
    
    def analyze_performance(self, daily_stats, trades):
        """Calculate performance metrics"""
        # Calculate returns
        daily_stats['returns'] = daily_stats['capital'].pct_change()
        
        # Trading metrics
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]
        
        total_trades = len(trades[trades['action'] == 'ENTRY'])
        winning_trades_count = len(winning_trades)
        
        # Performance metrics
        total_pnl = trades['pnl'].sum()
        win_rate = winning_trades_count / total_trades if total_trades > 0 else 0
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 else float('inf')
        
        # Portfolio metrics
        total_return = (daily_stats['capital'].iloc[-1] - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (252/len(daily_stats)) - 1
        volatility = daily_stats['returns'].std() * np.sqrt(252)
        sharpe_ratio = (annual_return) / volatility if volatility != 0 else 0
        
        # Drawdown analysis
        cumulative = (1 + daily_stats['returns']).cumprod()
        running_max = cumulative.expanding().max()
        drawdowns = cumulative / running_max - 1
        max_drawdown = abs(drawdowns.min())
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades_count,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_pnl': total_pnl
        }
    
    def plot_results(self, daily_stats, trades):
        """Plot backtest results"""
        # Use default style instead of seaborn
        plt.style.use('default')
        
        # Create figure with subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # Plot 1: Equity Curve
        ax1.plot(daily_stats.index, daily_stats['capital'], 
                color='blue', linewidth=1.5)
        ax1.set_title('Equity Curve', fontsize=12, pad=10)
        ax1.set_ylabel('Capital ($)', fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.tick_params(axis='both', labelsize=9)
        
        # Plot 2: Positions and Signals
        ax2.plot(daily_stats.index, daily_stats['price'], 
                color='black', linewidth=1.5, label='Price')
        
        # Plot entry/exit points
        entries = trades[trades['action'] == 'ENTRY']
        exits = trades[trades['action'] != 'ENTRY']
        
        ax2.scatter(entries['date'], entries['price'], 
                color='green', marker='^', s=100, label='Entry')
        ax2.scatter(exits['date'], exits['price'], 
                color='red', marker='v', s=100, label='Exit')
        
        ax2.set_title('Price with Entries/Exits', fontsize=12, pad=10)
        ax2.set_ylabel('Price', fontsize=10)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(fontsize=9)
        ax2.tick_params(axis='both', labelsize=9)
        
        # Plot 3: Growth Rate
        ax3.plot(daily_stats.index, daily_stats['growth_rate'], 
                color='purple', linewidth=1.5)
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax3.set_title('Growth Rate', fontsize=12, pad=10)
        ax3.set_ylabel('Annual Growth Rate (%)', fontsize=10)
        ax3.grid(True, linestyle='--', alpha=0.7)
        ax3.tick_params(axis='both', labelsize=9)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot
        plt.savefig(f'backtest_results.png', dpi=300, bbox_inches='tight')
        
        # Show plot
        plt.show()

def fetch_data(symbol: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Fetch data from Yahoo Finance"""
    try:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        data = yf.download(symbol, start=start_date, end=end_date)
        
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
            
        print(f"Fetched {len(data)} days of data for {symbol}")
        return data
        
    except Exception as e:
        raise Exception(f"Error fetching data: {str(e)}")

if __name__ == "__main__":
    # Set parameters
    symbol = "^GSPC"  # S&P 500
    start_date = "2022-01-01"  # Last 2 years
    initial_capital = 100000
    
    try:
        print(f"\nFetching data for {symbol}...")
        data = fetch_data(symbol, start_date)
        print(f"Data shape: {data.shape}")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")
        
        print("\nInitializing trading system...")
        system = PolynomialTradingSystem(
            data=data,
            period_years=2,
            max_position_size=0.25,
            min_rsquared=0.85
        )
        
        print("\nRunning backtest...")
        backtest = BacktestAnalyzer(initial_capital=initial_capital)
        daily_stats, trades = backtest.run_backtest(system, data)
        
        print("\nCalculating performance metrics...")
        performance = backtest.analyze_performance(daily_stats, trades)
        
        # Print detailed results
        print("\nPolynomial Regression Analysis:")
        print(f"Quadratic Coefficient: {system.quad_coef:.4f}")
        print(f"Linear Coefficient: {system.linear_coef:.4f}")
        print(f"R-squared: {system.r_squared:.4f}")
        print(f"Annual Volatility: {system.annual_volatility:.4f}")
        
        print("\nTrading Performance:")
        print(f"Total Trades: {performance['total_trades']}")
        print(f"Win Rate: {performance['win_rate']:.2%}")
        print(f"Profit Factor: {performance['profit_factor']:.2f}")
        print(f"Average Win: ${performance['avg_win']:,.2f}")
        print(f"Average Loss: ${performance['avg_loss']:,.2f}")
        
        print("\nPortfolio Performance:")
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Final Capital: ${daily_stats['capital'].iloc[-1]:,.2f}")
        print(f"Total Return: {performance['total_return']:.2%}")
        print(f"Annual Return: {performance['annual_return']:.2%}")
        print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {performance['max_drawdown']:.2%}")
        
        print("\nPlotting results...")
        backtest.plot_results(daily_stats, trades)
        
        print("\nSaving results to CSV...")
        daily_stats.to_csv(f"{symbol}_daily_stats.csv")
        trades.to_csv(f"{symbol}_trades.csv")
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"\nError occurred during analysis:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        import traceback
        traceback.print_exc()