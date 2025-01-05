"""
Configuration file for visualization layout settings
"""

LAYOUT_CONFIG = {
    'total_height': 1200,
    'lookback_days_ratio': 0.6,
    'chart_area': {
        'stock': {
            'domain': {'x': [0.05, 0.95], 'y': [0.65, 0.95]}  # Main chart top 40%
        },
        'non_stock': {
            'domain': {'x': [0.05, 0.95], 'y': [0.55, 0.95]}  # Main chart top 50%
        }
    },
    'tables': {
        'stock': {
            'analysis_summary': {
                'x': [0.05, 0.48],
                'y': [0.42, 0.55]
            },
            'trading_signals': {
                'x': [0.52, 0.95],
                'y': [0.42, 0.55]
            },
            'metrics': {
                'x': [0.05, 0.95],
                'y': [0.22, 0.35]
            },
            'growth': {
                'x': [0.05, 0.95],
                'y': [0.02, 0.15]
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
            }
        }
    },
    'annotations': {
        'stock': {
            'headers': {
                'chart': {'x': 0.05, 'y': 0.97},
                'analysis_summary': {'x': 0.05, 'y': 0.56},
                'trading_signals': {'x': 0.56, 'y': 0.56},
                'metrics': {'x': 0.05, 'y': 0.36},
                'growth': {'x': 0.05, 'y': 0.15}
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
        'retracement': dict(width=2, dash='dot'),
        'position': dict(width=2, dash='dot')
    },
    'marker_styles': {
        'crossover': dict(
            symbol='star',
            size=12,
            line=dict(width=1)
        )
    }
}