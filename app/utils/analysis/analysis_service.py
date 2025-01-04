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
        """Perform polynomial regression analysis and calculate scoring"""
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
                            'trend': {'score': 0, 'quad': 0, 'linear': 0},
                            'r2': 0,
                            'return': 0,
                            'volatility': 0
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
                    # Calculate S&P 500 regression
                    sp500_data['Log_Close'] = np.log(sp500_data['Close'])
                    X_sp = (sp500_data.index - sp500_data.index[0]).days.values.reshape(-1, 1)
                    y_sp = sp500_data['Log_Close'].values
                    X_sp_scaled = X_sp / (np.max(X_sp) * 1)
                    
                    poly_features = PolynomialFeatures(degree=2)
                    X_sp_poly = poly_features.fit_transform(X_sp_scaled)
                    sp500_model = LinearRegression()
                    sp500_model.fit(X_sp_poly, y_sp)
                    
                    # Calculate S&P 500 metrics
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
                    print("Using real S&P 500 parameters:", sp500_params)
                else:
                    sp500_params = {
                        'quad_coef': -0.1134,
                        'linear_coef': 0.4700,
                        'r_squared': 0.9505,
                        'annual_return': 0.2384,
                        'annual_volatility': 0.125
                    }
                    print("Using default S&P 500 parameters:", sp500_params)
            except Exception as sp_error:
                print(f"Error calculating S&P 500 parameters: {str(sp_error)}")
                sp500_params = {
                    'quad_coef': -0.1134,
                    'linear_coef': 0.4700,
                    'r_squared': 0.9505,
                    'annual_return': 0.2384,
                    'annual_volatility': 0.125
                }

            # 3. Perform regression on input data
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
                
                # Get coefficients
                coef = model.coef_
                intercept = model.intercept_
                max_x = np.max(X)
                
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
                            'trend': {'score': 0, 'quad': 0, 'linear': 0},
                            'r2': 0,
                            'return': 0,
                            'volatility': 0
                        }
                    }
                }

            # 4. Calculate scoring
            try:
                returns = data['Close'].pct_change().dropna()
                annual_return = returns.mean() * 252
                annual_volatility = returns.std() * np.sqrt(252)
                
                def score_trend(value, benchmark):
                    ratio = abs(value / benchmark)
                    if ratio >= 1.25: return 100
                    if ratio >= 1.10: return 80
                    if ratio >= 0.90: return 60
                    if ratio >= 0.75: return 40
                    return 20

                def score_metric(value, benchmark, thresholds, reverse=False):
                    if reverse:
                        if value <= benchmark * 0.8: return 100
                        if value <= benchmark: return 80
                        if value <= benchmark * 1.2: return 60
                        if value <= benchmark * 1.4: return 40
                        return 20
                    else:
                        if value >= benchmark * 1.2: return 100
                        if value >= benchmark: return 80
                        if value >= benchmark * 0.8: return 60
                        if value >= benchmark * 0.6: return 40
                        return 20

                # Calculate component scores
                if coef[2]<0 and coef[1]<0:
                    trend_score = 0
                quad_score = score_trend(coef[2], sp500_params['quad_coef'])
                linear_score = score_trend(coef[1], sp500_params['linear_coef'])
                trend_score = quad_score * 0.8 + linear_score * 0.2
                

                r2_score_val = score_metric(r2, sp500_params['r_squared'], [0.95, 0.90, 0.85])
                return_score = score_metric(annual_return, sp500_params['annual_return'], [1.2, 0.8, 0.6])
                vol_score = score_metric(annual_volatility, sp500_params['annual_volatility'], [0.8, 1.2, 1.4], True)

                # Calculate final score
                weights = {'trend': 0.4, 'r2': 0.20, 'return': 0.25, 'volatility': 0.15}
                final_score = (
                    trend_score * weights['trend'] +
                    r2_score_val * weights['r2'] +
                    return_score * weights['return'] +
                    vol_score * weights['volatility']
                )

                # Determine rating
                if final_score >= 90: rating = 'Excellent'
                elif final_score >= 75: rating = 'Very Good'
                elif final_score >= 60: rating = 'Good'
                elif final_score >= 40: rating = 'Fair'
                else: rating = 'Poor'

            except Exception as e:
                print(f"Error in scoring calculation: {str(e)}")
                final_score = 0
                rating = 'Error'
                trend_score = quad_score = linear_score = r2_score_val = return_score = vol_score = 0

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
                            'quad': float(quad_score),
                            'linear': float(linear_score)
                        },
                        'r2': float(r2_score_val),
                        'return': float(return_score),
                        'volatility': float(vol_score)
                    },
                    'benchmark_params': sp500_params,
                    'parameters': {
                        'quad_coef': float(coef[2]),
                        'linear_coef': float(coef[1]),
                        'r_squared': float(r2),
                        'annual_return': float(annual_return),
                        'annual_volatility': float(annual_volatility)
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
                        'trend': {'score': 0, 'quad': 0, 'linear': 0},
                        'r2': 0,
                        'return': 0,
                        'volatility': 0
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