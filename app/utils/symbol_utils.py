def normalize_ticker(symbol: str) -> str:
    """Convert TradingView symbol to Yahoo Finance symbol"""
    if symbol.startswith('TVC:'):
        # Handle indices
        index_map = {
            'TVC:HSI': '^HSI',    # Hang Seng Index
            'TVC:SSEC': '^SSEC',  # Shanghai Composite
            'TVC:SZSC': '^SZSC',  # Shenzhen Component
            'TVC:NDX': '^NDX',    # Nasdaq 100
            'TVC:SPX': '^GSPC',   # S&P 500
            'TVC:DJI': '^DJI'     # Dow Jones Industrial Average
        }
        return index_map.get(symbol, symbol.replace('TVC:', '^'))
    return symbol 