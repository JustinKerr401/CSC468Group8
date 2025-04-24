import yfinance as yf

def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        return hist["Close"].iloc[-1]
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return None
