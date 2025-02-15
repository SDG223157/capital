import re

def normalize_ticker(symbol: str) -> str:
    """Convert between TradingView and Yahoo Finance symbols"""
    # Handle Yahoo Finance indices to TradingView format
    if symbol.startswith('^'):
        yahoo_to_tv = {
            '^GSPC': 'TVC:SPX',    # S&P 500
            '^DJI': 'TVC:DJI',     # Dow Jones
            '^IXIC': 'TVC:NDX',    # NASDAQ 100
            '^HSI': 'TVC:HSI',     # Hang Seng
            '^N225': 'TVC:NI225',  # Nikkei 225
            '^FTSE': 'TVC:UKX',    # FTSE 100
            '^GDAXI': 'TVC:DEU40'  # DAX 40
        }
        return yahoo_to_tv.get(symbol, symbol)

    # Handle TradingView indices to Yahoo Finance format
    if symbol.startswith('TVC:'):
        tv_to_yahoo = {
            'TVC:HSI': '^HSI',     # Hang Seng Index
            'TVC:SSEC': '^SSEC',   # Shanghai Composite
            'TVC:SZSC': '^SZSC',   # Shenzhen Component
            'TVC:NDX': '^NDX',     # Nasdaq 100
            'TVC:SPX': '^GSPC',    # S&P 500
            'TVC:DJI': '^DJI'      # Dow Jones Industrial Average
        }
        return tv_to_yahoo.get(symbol, symbol.replace('TVC:', '^'))

    # Handle Yahoo Finance to TradingView conversion for stocks
    if re.match(r'^\d{4}\.HK$', symbol):
        return f"HKEX:{int(symbol.replace('.HK', ''))}"
    elif re.search(r'\.SS$', symbol):
        return f"SSE:{symbol.replace('.SS', '')}"
    elif re.search(r'\.SZ$', symbol):
        return f"SZSE:{symbol.replace('.SZ', '')}"
    
    # Convert TradingView to Yahoo Finance format for stocks
    if ':' in symbol:
        exchange, ticker = symbol.split(':')
        if exchange == 'HKEX':
            return f"{int(ticker):04d}.HK"
        elif exchange == 'SSE':
            return f"{ticker}.SS"
        elif exchange == 'SZSE':
            return f"{ticker}.SZ"
        return ticker
    
    return symbol 