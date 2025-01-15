# src/analysis/analysis_service.py

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from app.utils.data.data_service import DataService
import logging

class AnalysisService:
    @staticmethod
    def calculate_price_appreciation_pct(current_price, highest_price, lowest_price):
        """Calculate price appreciation percentage relative to range"""
        total_range = highest_price - lowest_price
        if total_range > 0:
            current_from_low = current_price - lowest_price
            return (current_from_low / total_range) * 100
        return 0

    @staticmethod
    def find_crossover_points(dates, series1, series2, prices):
        """Find points where two series cross each other"""
        crossover_points = []
        crossover_values = []
        crossover_directions = []
        crossover_prices = []
        
        s1 = np.array(series1)
        s2 = np.array(series2)
        
        diff = s1 - s2
        for i in range(1, len(diff)):
            if diff[i-1] <= 0 and diff[i] > 0:
                cross_value = (s1[i-1] + s2[i-1]) / 2
                crossover_points.append(dates[i])
                crossover_values.append(cross_value)
                crossover_directions.append('down')
                crossover_prices.append(prices[i])
            elif diff[i-1] >= 0 and diff[i] < 0:
                cross_value = (s1[i-1] + s2[i-1]) / 2
                crossover_points.append(dates[i])
                crossover_values.append(cross_value)
                crossover_directions.append('up')
                crossover_prices.append(prices[i])
        
        return crossover_points, crossover_values, crossover_directions, crossover_prices

    @staticmethod
    def format_regression_equation(coefficients, intercept, max_x):
        """Format regression equation string"""
        terms = []
        if coefficients[2] != 0:
            terms.append(f"{coefficients[2]:.4f}(x/{max_x})²")
        if coefficients[1] != 0:
            sign = "+" if coefficients[1] > 0 else ""
            terms.append(f"{sign}{coefficients[1]:.4f}(x/{max_x})")
        if intercept != 0:
            sign = "+" if intercept > 0 else ""
            terms.append(f"{sign}{intercept:.4f}")
        equation = "ln(y) = " + " ".join(terms)
        return equation

    @staticmethod
    def perform_polynomial_regression(data, future_days=180):
        """Perform polynomial regression analysis with three-component scoring"""
        try:
            # 1. Input validation
            if data is None or data.empty:
                print("Error: Input data is None or empty")
                return {
                    'predictions': [],
                    'upper_band': [],
                    'lower_band': [],
                    'r2': 0,
                    'coefficients': [0, 0, 0],
                    'intercept': 0,
                    'std_dev': 0,
                    'equation': "No data available",
                    'max_x': 0,
                    'total_score': {
                        'score': 0,
                        'rating': 'Error',
                        'components': {
                            'trend': {'score': 0, 'type': 'Unknown'},
                            'return': {'score': 0},
                            'volatility': {'score': 0}
                        }
                    }
                }

            # 2. Get S&P 500 benchmark parameters
            try:
                data_service = DataService()
                # end_date = datetime.now().strftime('%Y-%m-%d')
                end_date = data.index[-1].strftime('%Y-%m-%d')
                start_date = data.index[0].strftime('%Y-%m-%d')
                # start_date = (datetime.now() - timedelta(days=500)).strftime('%Y-%m-%d')
                
                sp500_data = data_service.get_historical_data('^GSPC', start_date, end_date)
                
                if sp500_data is not None and not sp500_data.empty:
                    sp500_data['Log_Close'] = np.log(sp500_data['Close'])
                    X_sp = (sp500_data.index - sp500_data.index[0]).days.values.reshape(-1, 1)
                    y_sp = sp500_data['Log_Close'].values
                    X_sp_scaled = X_sp / (np.max(X_sp) * 1)
                    
                    poly_features = PolynomialFeatures(degree=2)
                    X_sp_poly = poly_features.fit_transform(X_sp_scaled)
                    sp500_model = LinearRegression()
                    sp500_model.fit(X_sp_poly, y_sp)
                    
                    sp500_r2 = r2_score(y_sp, sp500_model.predict(X_sp_poly))
                    sp500_returns = sp500_data['Close'].pct_change().dropna()
                    sp500_annual_return = sp500_returns.mean() * 252
                    sp500_annual_volatility = sp500_returns.std() * np.sqrt(252)
                    
                    sp500_params = {
                        'quad_coef': sp500_model.coef_[2],
                        'linear_coef': sp500_model.coef_[1],
                        'r_squared': sp500_r2,
                        'annual_return': sp500_annual_return,
                        'annual_volatility': sp500_annual_volatility
                    }
                else:
                    sp500_params = {
                        'quad_coef': -0.1134,
                        'linear_coef': 0.4700,
                        'r_squared': 0.9505,
                        'annual_return': 0.2384,
                        'annual_volatility': 0.125
                    }
            except Exception as sp_error:
                print(f"Error calculating S&P 500 parameters: {str(sp_error)}")
                sp500_params = {
                    'quad_coef': -0.1134,
                    'linear_coef': 0.4700,
                    'r_squared': 0.9505,
                    'annual_return': 0.2384,
                    'annual_volatility': 0.125
                }

            # 3. Perform regression analysis
            try:
                data['Log_Close'] = np.log(data['Close'])
                X = (data.index - data.index[0]).days.values.reshape(-1, 1)
                y = data['Log_Close'].values
                X_scaled = X / (np.max(X) * 1)
                
                poly_features = PolynomialFeatures(degree=2)
                X_poly = poly_features.fit_transform(X_scaled)
                model = LinearRegression()
                model.fit(X_poly, y)
                
                coef = model.coef_
                intercept = model.intercept_
                max_x = np.max(X)
                
                # Calculate predictions
                X_future = np.arange(len(data) + future_days).reshape(-1, 1)
                X_future_scaled = X_future / np.max(X) * 1
                X_future_poly = poly_features.transform(X_future_scaled)
                y_pred_log = model.predict(X_future_poly)
                y_pred = np.exp(y_pred_log)
                
                # Calculate confidence bands
                residuals = y - model.predict(X_poly)
                std_dev = np.std(residuals)
                y_pred_upper = np.exp(y_pred_log + 2 * std_dev)
                y_pred_lower = np.exp(y_pred_log - 2 * std_dev)
                
                # Calculate R²
                r2 = r2_score(y, model.predict(X_poly))
                
                # Format equation
                equation = AnalysisService.format_regression_equation(coef, intercept, max_x)
                
            except Exception as e:
                print(f"Error in regression calculation: {str(e)}")
                return {
                    'predictions': data['Close'].values.tolist(),
                    'upper_band': data['Close'].values.tolist(),
                    'lower_band': data['Close'].values.tolist(),
                    'r2': 0,
                    'coefficients': [0, 0, 0],
                    'intercept': 0,
                    'std_dev': 0,
                    'equation': "Regression failed",
                    'max_x': len(data),
                    'total_score': {
                        'score': 0,
                        'rating': 'Error',
                        'components': {
                            'trend': {'score': 0, 'type': 'Unknown', 'details': {}},
                            'return': {'score': 0},
                            'volatility': {'score': 0}
                        }
                    }
                }

            # 4. Calculate scoring
            try:
                
                def evaluate_trend_score(quad_coef, linear_coef, r_squared):
                    """
                    Calculate trend score ranging from 0 (most bearish) to 100 (most bullish)
                    based on trend direction, strength, and credibility
                    """
                    try:
                        # 1. Calculate asset's own volatility for benchmarks
                        returns = data['Close'].pct_change().dropna()
                        annual_vol = returns.std() * np.sqrt(252)
                        period_days = len(data)
                        period_years = period_days / 252
                        
                        # Calculate benchmarks using asset's own volatility
                        vol_linear = annual_vol * np.sqrt(period_years)  
                        vol_quad = annual_vol / np.sqrt(period_days)
                        
                        # 2. Calculate base trend score (50 is neutral)
                        trend_score = 50
                        
                        # Linear component contribution (±25 points)
                        linear_impact = linear_coef / vol_linear
                        trend_score += 25 * min(1, max(-1, linear_impact))
                        
                        # Quadratic component contribution (±15 points)
                        quad_impact = quad_coef / vol_quad
                        if (quad_coef > 0 and linear_coef > 0) or (quad_coef < 0 and linear_coef < 0):
                            # Reinforcing trend
                            trend_score += 15 * min(1, max(-1, quad_impact))
                        else:
                            # Counteracting trend
                            trend_score -= 15 * min(1, max(-1, abs(quad_impact)))
                            
                        # 3. Apply strength multiplier based on R-squared
                        strength_multiplier = 0.5 + (0.5 * r_squared)  # Range: 0.5-1.0
                        
                        # 4. Calculate final score
                        final_score = trend_score * strength_multiplier
                        
                        # 5. Normalize to 0-100 range
                        final_score = min(100, max(0, final_score))
                        
                        # Calculate ratio for compatibility with existing code
                        ratio = abs(quad_coef / linear_coef) if linear_coef != 0 else float('inf')
                        
                        # Determine credibility level for compatibility
                        if r_squared >= 0.90: credibility_level = 5  # Very High
                        elif r_squared >= 0.80: credibility_level = 4  # High
                        elif r_squared >= 0.70: credibility_level = 3  # Moderate
                        elif r_squared >= 0.60: credibility_level = 2  # Low
                        else: credibility_level = 1  # Very Low
                        
                        return final_score, ratio, credibility_level
                        
                    except Exception as e:
                        print(f"Error in trend score calculation: {str(e)}")
                        return 50, 0, 1  # Return neutral score on error

                def score_metric(value, benchmark, metric_type='return'):
                    """
                    Score metrics based on type:
                    - Returns: Use difference in percentage points (5% steps)
                    - Volatility: Use ratio comparison
                    
                    Parameters:
                    value: actual value
                    benchmark: benchmark value
                    metric_type: 'return' or 'volatility'
                    """
                    if metric_type == 'return':
                        # For returns, use absolute difference in percentage points
                        diff = (value - benchmark) * 100  # Convert to percentage points
                        
                        # Score based on 5% steps from -30% to +30%
                        
                        if diff >= 40: return 100
                        if diff >= 35: return 95
                        if diff >= 30: return 90    # ≥30% better than benchmark
                        if diff >= 25: return 85
                        if diff >= 20: return 80
                        if diff >= 15: return 75
                        if diff >= 10: return 70
                        if diff >= 5:  return 65
                        if diff >= 0:  return 60     # Meeting benchmark
                        if diff >= -5: return 45
                        if diff >= -10: return 40
                        if diff >= -15: return 30
                        if diff >= -20: return 20
                        if diff >= -25: return 10
                        return 5                     # >25% worse than benchmark
                        
                    else:  # volatility
                        # For volatility, use ratio (lower is better)
                        ratio = value / benchmark
                        
                        if ratio <= 0.6: return 100    # 40% or less volatility
                        if ratio <= 0.7: return 90
                        if ratio <= 0.8: return 85
                        if ratio <= 0.9: return 80
                        if ratio <= 1.0: return 75     # Equal to benchmark
                        if ratio <= 1.1: return 70
                        if ratio <= 1.2: return 65
                        if ratio <= 1.3: return 60
                        if ratio <= 1.4: return 55
                        if ratio <= 1.5: return 50
                        return 40                       # >50% more volatile

               
                # Calculate returns and volatility
                returns = data['Close'].pct_change().dropna()
                annual_return = returns.mean() * 252
                annual_volatility = returns.std() * np.sqrt(252)
                
                # Calculate trend score
                trend_score, ratio, credibility_level = evaluate_trend_score(coef[2], coef[1], r2)
                
                # Calculate other scores
                 # Usage in scoring section:
                return_score = score_metric(annual_return, sp500_params['annual_return'], 'return')
                vol_score = score_metric(annual_volatility, sp500_params['annual_volatility'], 'volatility')
                
                # Calculate raw score
                weights = {'trend': 0.4, 'return': 0.4, 'volatility': 0.20}
                raw_score = (
                    trend_score * weights['trend'] +
                    return_score * weights['return'] +
                    vol_score * weights['volatility']
                )

                # Calculate SP500's raw score
                sp500_trend_score, _, _ = evaluate_trend_score(
                    sp500_params['quad_coef'], 
                    sp500_params['linear_coef'],
                    sp500_params['r_squared']
                )
                sp500_return_score = score_metric(sp500_params['annual_return'], sp500_params['annual_return'], 'return')
                sp500_vol_score = score_metric(sp500_params['annual_volatility'], sp500_params['annual_volatility'], 'volatility')

                sp500_raw_score = (
                    sp500_trend_score * weights['trend'] +
                    sp500_return_score * weights['return'] +
                    sp500_vol_score * weights['volatility']
                )
                scaling_factor =  75/ sp500_raw_score

                # Calculate final scaled score
                final_score = min(98, raw_score * scaling_factor)

                # Determine rating
                if final_score >= 90: rating = 'Excellent'
                elif final_score >= 75: rating = 'Very Good'
                elif final_score >= 65: rating = 'Good'
                elif final_score >= 40: rating = 'Fair'
                else: rating = 'Poor'

            except Exception as e:
                print(f"Error in scoring calculation: {str(e)}")
                return_score = vol_score = trend_score = final_score = 0
                rating = 'Error'
                ratio = 0
                credibility_level = 0

            # 5. Return complete results
            return {
                'predictions': y_pred.tolist(),
                'upper_band': y_pred_upper.tolist(),
                'lower_band': y_pred_lower.tolist(),
                'r2': float(r2),
                'coefficients': coef.tolist(),
                'intercept': float(intercept),
                'std_dev': float(std_dev),
                'equation': equation,
                'max_x': int(max_x),
                'total_score': {
                    'score': float(final_score),
                    'raw_score': float(raw_score),
                    'rating': rating,
                    'components': {
                        'trend': {
                            'score': float(trend_score),
                            'details': {
                                'ratio': float(ratio),
                                'credibility_level': credibility_level,
                                'quad_coef': float(coef[2]),
                                'linear_coef': float(coef[1])
                            }
                        },
                        'return': {
                            'score': float(return_score),
                            'value': float(annual_return)
                        },
                        'volatility': {
                            'score': float(vol_score),
                            'value': float(annual_volatility)
                        }
                    },
                    'scaling': {
                        'factor': float(scaling_factor),
                        'sp500_base': float(sp500_raw_score)
                    },
                    'weights': weights
                }
            }

        except Exception as e:
            print(f"Error in polynomial regression: {str(e)}")
            return {
                'predictions': data['Close'].values.tolist() if data is not None else [],
                'upper_band': data['Close'].values.tolist() if data is not None else [],
                'lower_band': data['Close'].values.tolist() if data is not None else [],
                'r2': 0,
                'coefficients': [0, 0, 0],
                'intercept': 0,
                'std_dev': 0,
                'equation': "Error occurred",
                'max_x': len(data) if data is not None else 0,
                'total_score': {
                    'score': 0,
                    'raw_score': 0,
                    'rating': 'Error',
                    'components': {
                        'trend': {'score': 0, 'details': {}},
                        'return': {'score': 0, 'value': 0},
                        'volatility': {'score': 0, 'value': 0}
                    }
                }
            }
    
    
    @staticmethod
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

    
    
    @staticmethod
    def calculate_rolling_r2(data, lookback_days=365):
        """Calculate rolling R-square values for regression analysis"""
        analysis_dates = []
        r2_values = []
        
        for current_date in data.index:
            year_start = current_date - timedelta(days=lookback_days)
            mask = (data.index <= current_date)
            period_data = data.loc[mask].copy()  # Create explicit copy
            
            if (current_date - period_data.index[0]).days > lookback_days:
                period_data = period_data[period_data.index > year_start]
            
            if len(period_data) < 20:
                continue
                
            try:
                # Calculate log returns
                period_data.loc[:, 'Log_Close'] = np.log(period_data['Close'])
                
                X = (period_data.index - period_data.index[0]).days.values.reshape(-1, 1)
                y = period_data['Log_Close'].values
                X_scaled = X / (np.max(X) * 1)
                
                poly_features = PolynomialFeatures(degree=2)
                X_poly = poly_features.fit_transform(X_scaled)
                model = LinearRegression()
                model.fit(X_poly, y)
                
                r2 = r2_score(y, model.predict(X_poly))
                
                analysis_dates.append(current_date)
                r2_values.append(r2 * 100)
                
            except Exception as e:
                print(f"Error calculating R² for {current_date}: {str(e)}")
                continue
        
        return analysis_dates, r2_values

    
    @staticmethod
    def analyze_stock_data(data, crossover_days=365, lookback_days=365):
        """Perform comprehensive stock analysis"""
        logger = logging.getLogger(__name__)
        logger.debug(f"Starting stock analysis with shape: {data.shape}")
        
        try:
            result_data = []
            
            for current_date in data.index:
                # Get data for R-square calculation (lookback_days)
                r2_start = current_date - timedelta(days=lookback_days)
                r2_data = data.loc[data.index <= current_date].copy()
                if (current_date - r2_data.index[0]).days > lookback_days:
                    r2_data = r2_data[r2_data.index > r2_start]
                
                # Get data for technical indicators (crossover_days)
                tech_start = current_date - timedelta(days=crossover_days)
                period_data = data.loc[data.index <= current_date].copy()
                if (current_date - period_data.index[0]).days > crossover_days:
                    period_data = period_data[period_data.index > tech_start]
                
                if len(period_data) < 20:  # Minimum data points needed
                    continue
                
                # Calculate technical metrics using crossover window
                current_price = period_data['Close'].iloc[-1]
                highest_price = period_data['Close'].max()
                lowest_price = period_data['Close'].min()
                
                # Calculate retracement ratio
                total_move = highest_price - lowest_price
                if total_move > 0:
                    current_retracement = highest_price - current_price
                    ratio = (current_retracement / total_move) * 100
                else:
                    ratio = 0
                
                # Calculate price appreciation
                appreciation_pct = AnalysisService.calculate_price_appreciation_pct(
                    current_price, highest_price, lowest_price)
                
                # Calculate R-square using lookback window
                try:
                    if len(r2_data) >= 20:  # Ensure enough data for R² calculation
                        r2_data.loc[:, 'Log_Close'] = np.log(r2_data['Close'])
                        X = (r2_data.index - r2_data.index[0]).days.values.reshape(-1, 1)
                        y = r2_data['Log_Close'].values
                        X_scaled = X / np.max(X)
                        
                        poly_features = PolynomialFeatures(degree=2)
                        X_poly = poly_features.fit_transform(X_scaled)
                        model = LinearRegression()
                        model.fit(X_poly, y)
                        
                        r2 = r2_score(y, model.predict(X_poly))
                        r2_pct = r2 * 100
                        
                        # logger.debug(f"R² for {current_date}: {r2_pct:.2f}% (using {len(r2_data)} days)")
                    else:
                        r2_pct = None
                        # logger.debug(f"Insufficient data for R² calculation at {current_date}")
                        
                except Exception as e:
                    logger.error(f"Error calculating R² for {current_date}: {str(e)}")
                    r2_pct = None
                
                # Store results
                result_data.append({
                    'Date': current_date,
                    'Close': current_price,
                    'High': highest_price,
                    'Low': lowest_price,
                    'Retracement_Ratio_Pct': ratio,
                    'Price_Position_Pct': appreciation_pct,
                    'R2_Pct': r2_pct
                })
            
            # Create DataFrame
            df = pd.DataFrame(result_data)
            df.set_index('Date', inplace=True)
            
            # Copy original OHLCV columns
            for col in ['Open', 'Volume', 'Dividends', 'Stock Splits']:
                if col in data.columns:
                    df[col] = data[col]
                    
            logger.info("Analysis complete")
            # if 'R2_Pct' in df.columns:
            #     valid_r2 = df['R2_Pct'].dropna()
                # if not valid_r2.empty:
                #     logger.info(f"R² Stats - Mean: {valid_r2.mean():.2f}%, Min: {valid_r2.min():.2f}%, Max: {valid_r2.max():.2f}%")
            
            return df
            
        except Exception as e:
            logger.error(f"Error in analyze_stock_data: {str(e)}", exc_info=True)
            raise
        
        
    @staticmethod
    def analyze_stock_data_old(data, crossover_days=365):
        """Perform comprehensive stock analysis"""
        analysis_dates = []
        ratios = []
        prices = []
        highest_prices = []
        lowest_prices = []
        appreciation_pcts = []
        
        for current_date in data.index:
            year_start = current_date - timedelta(days=crossover_days)
            mask = (data.index <= current_date)  # Include all data up to current date
            period_data = data.loc[mask]
            
            # If we have more than crossover_days of data, limit to the lookback period
            if (current_date - period_data.index[0]).days > crossover_days:
                period_data = period_data[period_data.index > year_start]
            
            # Only calculate if we have at least some minimum data points
            if len(period_data) < 2:  # Reduced minimum requirement to 2 points
                continue
                
            current_price = period_data['Close'].iloc[-1]
            highest_price = period_data['Close'].max()
            lowest_price = period_data['Close'].min()
            
            # Calculate ratio
            total_move = highest_price - lowest_price
            if total_move > 0:
                current_retracement = highest_price - current_price
                ratio = (current_retracement / total_move) * 100
            else:
                ratio = 0
                
            # Calculate appreciation percentage
            appreciation_pct = AnalysisService.calculate_price_appreciation_pct(
                current_price, highest_price, lowest_price)
            
            analysis_dates.append(current_date)
            ratios.append(ratio)
            prices.append(current_price)
            highest_prices.append(highest_price)
            lowest_prices.append(lowest_price)
            appreciation_pcts.append(appreciation_pct)
            
        return pd.DataFrame({
            'Date': analysis_dates,
            'Price': prices,
            'High': highest_prices,
            'Low': lowest_prices,
            'Retracement_Ratio_Pct': ratios,
            'Price_Position_Pct': appreciation_pcts
        })