# src/analysis/analysis_service.py

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from app.utils.data.data_service import DataService

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
        """Perform polynomial regression analysis with comprehensive trend analysis and scoring"""
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
                            'trend': {
                                'score': 0,
                                'type': 'Unknown',
                                'details': {}
                            },
                            'return': {'score': 0},
                            'volatility': {'score': 0}
                        }
                    }
                }

            # 2. Get S&P 500 benchmark parameters
            try:
                data_service = DataService()
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
                
                sp500_data = data_service.get_historical_data('^GSPC', start_date, end_date)
                
                if sp500_data is not None and not sp500_data.empty:
                    # Calculate using sequential trading days for SP500
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
                        'quad_coef': 0.1080,
                        'linear_coef': 0.9646,
                        'r_squared': 0.9404,
                        'annual_return': 0.1127,
                        'annual_volatility': 0.178
                    }
            except Exception as sp_error:
                print(f"Error calculating S&P 500 parameters: {str(sp_error)}")
                sp500_params = {
                    'quad_coef': 0.1080,
                    'linear_coef': 0.9646,
                    'r_squared': 0.9404,
                    'annual_return': 0.1127,
                    'annual_volatility': 0.178
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
                
                # Calculate predictions
                X_future = np.arange(len(data) + future_days).reshape(-1, 1)
                X_future_poly = poly_features.transform(X_future)
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
                coef = model.coef_
                intercept = model.intercept_
                max_x = len(data) - 1
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
                    """Calculate trend score based on trend direction, strength, and credibility"""
                    ratio = abs(quad_coef / linear_coef) if linear_coef != 0 else float('inf')
                    
                    # Check credibility
                    if r_squared >= 0.90:
                        credibility_level = 5  # Very High
                    elif r_squared >= 0.80:
                        credibility_level = 4  # High
                    elif r_squared >= 0.70:
                        credibility_level = 3  # Moderate
                    elif r_squared >= 0.60:
                        credibility_level = 2  # Low
                    else:
                        credibility_level = 1  # Very Low

                    # Determine base trend score
                    if quad_coef > 0:
                        if linear_coef > 0:  # Both positive
                            if ratio < 0.5:  # Strong linear uptrend
                                base_score = 90
                            elif ratio < 2:  # Balanced uptrend
                                base_score = 80
                            else:  # Strong quadratic uptrend
                                base_score = 70
                        else:  # quad > 0, linear < 0
                            if ratio > 2:  # Quadratic dominates
                                base_score = 65
                            else:
                                base_score = 50
                    else:  # quad < 0
                        if linear_coef < 0:  # Both negative
                            if ratio < 0.5:  # Strong linear downtrend
                                base_score = 30
                            elif ratio < 2:  # Balanced downtrend
                                base_score = 20
                            else:  # Strong quadratic downtrend
                                base_score = 10
                        else:  # quad < 0, linear > 0
                            if ratio > 2:  # Quadratic dominates
                                base_score = 25
                            else:
                                base_score = 40

                    # Adjust score based on credibility
                    credibility_adjustment = (credibility_level - 3) * 5
                    final_score = min(100, max(0, base_score + credibility_adjustment))

                    return final_score, ratio, credibility_level

                def score_metric(value, benchmark, reverse=False):
                    """Score metrics with granular thresholds"""
                    ratio = value / benchmark
                    
                    if reverse:
                        if ratio <= 0.6: return 100
                        if ratio <= 0.7: return 90
                        if ratio <= 0.8: return 80
                        if ratio <= 0.9: return 70
                        if ratio <= 1.0: return 60
                        if ratio <= 1.1: return 50
                        if ratio <= 1.2: return 40
                        if ratio <= 1.3: return 30
                        if ratio <= 1.4: return 20
                        if ratio <= 1.5: return 10
                        return 0
                    else:
                        if ratio >= 1.4: return 100
                        if ratio >= 1.3: return 90
                        if ratio >= 1.2: return 80
                        if ratio >= 1.1: return 70
                        if ratio >= 1.0: return 60
                        if ratio >= 0.9: return 50
                        if ratio >= 0.8: return 40
                        if ratio >= 0.7: return 30
                        if ratio >= 0.6: return 20
                        if ratio >= 0.5: return 10
                        return 0

                # Calculate returns and volatility
                returns = data['Close'].pct_change().dropna()
                annual_return = returns.mean() * 252
                annual_volatility = returns.std() * np.sqrt(252)
                
                # Calculate trend score
                trend_score, ratio, credibility_level = evaluate_trend_score(coef[2], coef[1], r2)
                
                # Calculate other scores
                return_score = score_metric(annual_return, sp500_params['annual_return'])
                vol_score = score_metric(annual_volatility, sp500_params['annual_volatility'], reverse=True)

                # Calculate raw score
                weights = {'trend': 0.45, 'return': 0.30, 'volatility': 0.25}
                raw_score = (
                    trend_score * weights['trend'] +
                    return_score * weights['return'] +
                    vol_score * weights['volatility']
                )

                # Calculate scaling factor to make SP500 = 70
                sp500_raw_score = 69  # SP500's raw score from its own parameters
                scaling_factor = 70 / sp500_raw_score

                # Calculate final scaled score
                final_score = raw_score * scaling_factor

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
    def analyze_stock_data(data, lookback_days=180):
        """Perform comprehensive stock analysis"""
        analysis_dates = []
        ratios = []
        prices = []
        highest_prices = []
        lowest_prices = []
        appreciation_pcts = []
        
        for current_date in data.index:
            year_start = current_date - timedelta(days=lookback_days)
            mask = (data.index > year_start) & (data.index <= current_date)
            period_data = data.loc[mask]
            
            if len(period_data) < 20:
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