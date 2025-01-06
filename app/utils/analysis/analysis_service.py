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
        """Perform polynomial regression analysis with granular scoring"""
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
                    sp500_data['Log_Close'] = np.log(sp500_data['Close'])
                    # X_sp = np.arange(len(sp500_data)).reshape(-1, 1)
                    X_sp = (sp500_data.index - sp500_data.index[0]).days.values.reshape(-1, 1)
                    y_sp = sp500_data['Log_Close'].values
                    # X_sp_scaled = X_sp / (len(sp500_data) - 1)  # Scale by number of trading days
    
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
                # X = np.arange(len(data)).reshape(-1, 1)  # Sequential trading days
                X = (data.index - data.index[0]).days.values.reshape(-1, 1)
                y = data['Log_Close'].values
                # X_scaled = X / (len(data) - 1)  # Scale by number of trading days
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

            # 4. Calculate scoring with granular thresholds
            try:
                def evaluate_trend(quad_coef, linear_coef, r_squared):
                    """Evaluate trend with granular scoring (0-100 in steps of 10)"""
                    # Check credibility levels
                    if r_squared >= 0.90:
                        credibility = "Very High"
                    elif r_squared >= 0.80:
                        credibility = "High"
                    elif r_squared >= 0.70:
                        credibility = "Moderate"
                    elif r_squared >= 0.60:
                        credibility = "Low"
                    else:
                        credibility = "Very Low"

                    # Calculate ratio for strength
                    ratio =  linear_coef/quad_coef if quad_coef != 0 else float('inf')
                    abs_ratio = abs(ratio)

                    # Determine trend strength
                    if abs_ratio > 5:
                        strength = "Very Strong"
                    elif abs_ratio > 3:
                        strength = "Strong"
                    elif abs_ratio > 1:
                        strength = "Moderate"
                    elif abs_ratio > 0.5:
                        strength = "Weak"
                    else:
                        strength = "Very Weak"

                    # Determine trend direction
                    if quad_coef > 0 and linear_coef > 0:
                        trend_type = "Up"
                    elif quad_coef < 0 and linear_coef < 0:
                        trend_type = "Down"
                    elif ratio < 0:  # Different signs
                        if abs_ratio > 2 and quad_coef < 0:
                            trend_type = "Up"
                        elif abs_ratio < 0.5 and linear_coef > 0:
                            trend_type = "Up"
                        else:
                            trend_type = "Down"
                    else:
                        trend_type = "None"

                    # Score assignment based on scenario
                    if trend_type == "None" or abs_ratio < 0.1:
                        score = 20
                        desc = "No Clear Trend"
                    elif trend_type == "Up":
                        if strength == "Very Strong":
                            if credibility == "Very High": score = 100
                            elif credibility == "High": score = 90
                            elif credibility == "Moderate": score = 80
                            elif credibility == "Low": score = 70
                            else: score = 60
                        elif strength == "Strong":
                            if credibility == "Very High": score = 90
                            elif credibility == "High": score = 80
                            elif credibility == "Moderate": score = 70
                            elif credibility == "Low": score = 60
                            else: score = 50
                        elif strength == "Moderate":
                            if credibility == "Very High": score = 80
                            elif credibility == "High": score = 70
                            elif credibility == "Moderate": score = 60
                            elif credibility == "Low": score = 50
                            else: score = 40
                        else:  # Weak or Very Weak
                            if r_squared >= 0.80: score = 30
                            else: score = 20
                        desc = f"{strength} Uptrend ({credibility} Credibility)"
                    else:  # Down trend
                        if strength == "Very Strong":
                            if credibility == "Very High": score = 0
                            elif credibility == "High": score = 10
                            elif credibility == "Moderate": score = 20
                            elif credibility == "Low": score = 30
                            else: score = 40
                        elif strength == "Strong":
                            if credibility == "Very High": score = 10
                            elif credibility == "High": score = 20
                            elif credibility == "Moderate": score = 20
                            elif credibility == "Low": score = 20
                            else: score = 20
                        elif strength == "Moderate":
                            if credibility == "Very High": score = 20
                            elif credibility == "High": score = 20
                            elif credibility == "Moderate": score = 20
                            elif credibility == "Low": score = 20
                            else: score = 20
                        else:  # Weak or Very Weak
                            if r_squared >= 0.80: score = 30
                            else: score = 20
                        desc = f"{strength} Downtrend ({credibility} Credibility)"

                    return desc, score, {
                        'direction': trend_type,
                        'strength': strength,
                        'credibility': credibility,
                        'ratio': abs_ratio,
                        'r_squared': r_squared
                    }

                def score_metric(value, benchmark, reverse=False):
                    """Score metrics with granular thresholds (0-100)"""
                    ratio = value / benchmark
                    
                    if reverse:
                        # For metrics where lower is better (e.g., volatility)
                        if ratio <= 0.6: return 100    # 40% or more below benchmark
                        if ratio <= 0.7: return 90     # 30-40% below benchmark
                        if ratio <= 0.8: return 80     # 20-30% below benchmark
                        if ratio <= 0.9: return 75     # 10-20% below benchmark
                        if ratio <= 1.0: return 70     # 0-10% below benchmark
                        if ratio <= 1.1: return 50     # 0-10% above benchmark
                        if ratio <= 1.2: return 40     # 10-20% above benchmark
                        if ratio <= 1.3: return 30     # 20-30% above benchmark
                        if ratio <= 1.4: return 20     # 30-40% above benchmark
                        if ratio <= 1.5: return 10     # 40-50% above benchmark
                        return 0                       # More than 50% above benchmark
                    else:
                        # For metrics where higher is better (e.g., returns)
                        if ratio >= 1.4: return 100    # 40% or more above benchmark
                        if ratio >= 1.3: return 90     # 30-40% above benchmark
                        if ratio >= 1.2: return 80     # 20-30% above benchmark
                        if ratio >= 1.1: return 75     # 10-20% above benchmark
                        if ratio >= 1.0: return 70     # 0-10% above benchmark
                        if ratio >= 0.9: return 50     # 0-10% below benchmark
                        if ratio >= 0.8: return 40     # 10-20% below benchmark
                        if ratio >= 0.7: return 30     # 20-30% below benchmark
                        if ratio >= 0.6: return 20     # 30-40% below benchmark
                        if ratio >= 0.5: return 10     # 40-50% below benchmark
                        return 0                       # More than 50% below benchmark

                # Calculate returns and volatility
                returns = data['Close'].pct_change().dropna()
                annual_return = returns.mean() * 252
                annual_volatility = returns.std() * np.sqrt(252)
                
                # Get trend evaluation
                trend_type, trend_score, trend_details = evaluate_trend(coef[2], coef[1], r2)
                
                # Calculate other component scores
                return_score = score_metric(annual_return, sp500_params['annual_return'])
                vol_score = score_metric(annual_volatility, sp500_params['annual_volatility'], reverse=True)

                # Calculate final score with weights
                # weights = {'trend': 0.40, 'return': 0.40, 'volatility': 0.20}
                # final_score = (
                #     trend_score * weights['trend'] +
                #     return_score * weights['return'] +
                #     vol_score * weights['volatility']
                # )

                # First calculate SP500's own raw score using the benchmark parameters
                _, sp500_trend_score, _ = evaluate_trend(
                    sp500_params['quad_coef'], 
                    sp500_params['linear_coef'], 
                    sp500_params['r_squared']
                )
                sp500_return_score = score_metric(sp500_params['annual_return'], sp500_params['annual_return'])  # Should be 60
                sp500_vol_score = score_metric(sp500_params['annual_volatility'], sp500_params['annual_volatility'], reverse=True)  # Should be 60

                # Calculate SP500's raw score
                weights = {'trend': 0.45, 'return': 0.35, 'volatility': 0.20}
                sp500_raw_score = (
                    sp500_trend_score * weights['trend'] +
                    sp500_return_score * weights['return'] +
                    sp500_vol_score * weights['volatility']
                )

                # Calculate scaling factor to make SP500 score 70
                sp500_target_score = 70
                scaling_factor = sp500_target_score / sp500_raw_score

# Then use this scaling factor for the asset's score
                final_score = (
                    trend_score * weights['trend'] +
                    return_score * weights['return'] +
                    vol_score * weights['volatility']
                ) * scaling_factor
                # Determine rating
                if final_score >= 90: rating = 'Excellent'
                elif final_score >= 75: rating = 'Very Good'
                elif final_score >= 60: rating = 'Good'
                elif final_score >= 40: rating = 'Fair'
                else: rating = 'Poor'

            except Exception as e:
                print(f"Error in scoring calculation: {str(e)}")
                trend_type = "Error"
                trend_score = return_score = vol_score = final_score = 0
                rating = 'Error'
                trend_details = {}

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
                    'rating': rating,
                    'components': {
                        'trend': {
                            'score': float(trend_score),
                            'type': trend_type,
                            'details': trend_details
                        },
                        'return': {
                            'score': float(return_score),
                            'value': float(annual_return),
                            'benchmark': float(sp500_params['annual_return'])
                        },
                        'volatility': {
                            'score': float(vol_score),
                            'value': float(annual_volatility),
                            'benchmark': float(sp500_params['annual_volatility'])
                        }
                    },
                    'weights': weights,
                    'parameters': {
                        'quad_coef': float(coef[2]),
                        'linear_coef': float(coef[1]),
                        'r_squared': float(r2)
                    }
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
                    'rating': 'Error',
                    'components': {
                        'trend': {
                            'score': 0,
                            'type': 'Unknown',
                            'details': {}
                        },
                        'return': {
                            'score': 0,
                            'value': 0,
                            'benchmark': 0
                        },
                        'volatility': {
                            'score': 0,
                            'value': 0,
                            'benchmark': 0
                        }
                    },
                    'weights': {'trend': 0.45, 'return': 0.30, 'volatility': 0.25},
                    'parameters': {
                        'quad_coef': 0,
                        'linear_coef': 0,
                        'r_squared': 0
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