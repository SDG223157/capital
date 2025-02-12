"""
Configuration file for visualization layout settings
"""

LAYOUT_CONFIG = {
    'total_height': 1200,
    'lookback_days_ratio': 0.6,
    'chart_area': {
        'stock': {
            'domain': {'x': [0.05, 0.95], 'y': [0.60, 0.95]}  # Main chart top 35%
        },
        'non_stock': {
            'domain': {'x': [0.05, 0.95], 'y': [0.55, 0.95]}  # Main chart top 50%
        }
    },
    'tables': {
        'stock': {
            'company_info': {
                'x': [0.05, 0.48],
                'y': [0.42, 0.52]  # Company info table
            },
            'analysis_summary': {
                'x': [0.52, 0.95],
                'y': [0.42, 0.52]  # Analysis summary table
            },
            'trading_signals': {
                'x': [0.05, 0.95],
                'y': [0.27, 0.37]  # Trading signals table
            },
            'metrics': {
                'x': [0.05, 0.95],
                'y': [0.12, 0.22]  # Metrics table
            },
            'growth': {
                'x': [0.05, 0.95],
                'y': [0.02, 0.07]  # Growth table
            }
        },
        'non_stock': {
            'analysis_summary': {
                'x': [0.05, 0.48],
                'y': [0.12, 0.44]
            },
            'trading_signals': {
                'x': [0.52, 0.95],
                'y': [0.12, 0.44]
            },
            'analysis_summary': {
                'x': [0.52, 0.98],
                'y': [0.27, 0.45]
            }
        }
    },
    'annotations': {
        'stock': {
            'headers': {
                'chart': {'x': 0.05, 'y': 0.97},
                'company_info_title': {'x': 0.05, 'y': 0.53, 'text': 'Company Information'},  # Just above company_info table
                'analysis_summary': {'x': 0.52, 'y': 0.53},  # Just above analysis_summary table
                'trading_signals': {'x': 0.05, 'y': 0.38},  # Just above trading_signals table
                'metrics': {'x': 0.05, 'y': 0.23},  # Just above metrics table
                'growth': {'x': 0.05, 'y': 0.08}  # Just above growth table
            }
        },
        'non_stock': {
            'headers': {
                'chart': {'x': 0.05, 'y': 0.97},
                'analysis_summary': {'x': 0.05, 'y': 0.46},
                'trading_signals': {'x': 0.56, 'y': 0.46}
            }
        }
    },
    'spacing': {
        'vertical_gap': 0.05,
        'horizontal_gap': 0.04,
        'header_gap': 0.01,
        'margin': {
            'top': 0.05,
            'bottom': 0.05,
            'left': 0.05,
            'right': 0.05
        }
    }
}

# Table style configuration
TABLE_STYLE = {
    'stock': {
        'header': {
            'fill_color': 'lightgrey',
            'font': dict(size=12),
            'align': 'left',
            'height': 30
        },
        'cells': {
            'font': dict(size=11),
            'align': 'left',
            'height': 30
        }
    },
    'non_stock': {
        'header': {
            'fill_color': 'lightgrey',
            'font': dict(size=13),
            'align': 'left',
            'height': 35  # Double height for non-stocks
        },
        'cells': {
            'font': dict(size=12),
            'align': 'left',
            'height': 35  # Double height for non-stocks
        }
    }
}

# Chart style configuration
CHART_STYLE = {
    'colors': {
        'price_line': 'green',
        'regression_line': 'blue',
        'confidence_band': 'lightblue',
        'retracement_line': 'purple',
        'position_line': 'orange',
        'bullish_marker': 'green',
        'bearish_marker': 'red'
    },
    'line_styles': {
        'price': dict(width=3),
        'regression': dict(width=2, dash='dash'),
        'bands': dict(width=1),
        'retracement': dict(width=1, dash='dot'),
        'position': dict(width=1, dash='dot')
    },
    'marker_styles': {
        'crossover': dict(
            symbol='star',
            size=8,
            line=dict(width=1)
        )
    }
}