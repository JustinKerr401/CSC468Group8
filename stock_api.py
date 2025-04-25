# stock_api.py

import yfinance as yf

def get_stock_price(symbol):
    print(f"Fetching price for {symbol}...")  # Add this for debugging
    try:
        stock = yf.Ticker(symbol)
        stock_data = stock.history(period="1d")
        if stock_data.empty:
            print(f"KEYWORD No data for {symbol}")  # Print message if no data is returned
            return None
        current_price = stock_data['Close'].iloc[-1]
        print(f"KEYWORD Fetched price for {symbol}: {current_price}")  # Print fetched price
        return current_price
    except Exception as e:
        print(f"KEYWORD Error fetching data for {symbol}: {e}")
        return None
