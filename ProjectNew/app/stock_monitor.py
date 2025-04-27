from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import yfinance as yf
import json
import os
import pandas as pd
from pytz import timezone, utc

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = "users.json"

# MongoDB setup
client = MongoClient("mongodb://mongo:27017/")
db = client.stock_tracker
price_cache = db.price_cache
stock_list = db.stock_list

# Track last update time
last_price_update_time = None

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

users = load_users()

def load_stock_list_from_db():
    return [doc['symbol'] for doc in stock_list.find()]

def update_global_price_cache():
    global last_price_update_time
    symbols = load_stock_list_from_db()
    now = datetime.utcnow()

    try:
        data = yf.download(
            " ".join(symbols),
            period='1d',
            interval='1m',
            threads=True,
            progress=False
        )
        if isinstance(data.columns, pd.MultiIndex):
            for symbol in symbols:
                try:
                    series = data["Close"][symbol].dropna()
                    if not series.empty:
                        price = series.iloc[-1]
                        price_cache.update_one(
                            {"symbol": symbol},
                            {"$set": {"price": round(price, 2), "last_updated": now}},
                            upsert=True
                        )
                except Exception as e:
                    print(f"[Cache Error] {symbol}: {e}")
        else:
            print("[Cache Error] Unexpected data format returned by yfinance")
    except Exception as e:
        print(f"[Download Error] {e}")

    last_price_update_time = now
    print("✅ Updated global price cache.")

def get_cached_prices(symbols):
    """
    Always return whatever is in the cache for each symbol,
    so users see the last half-hour snapshot even if slightly older.
    """
    cached = price_cache.find({"symbol": {"$in": symbols}})
    return {doc['symbol']: doc['price'] for doc in cached}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('portfolio'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash('Username already exists!', 'danger')
        else:
            users[username] = {'password': password, 'stocks': {}}
            save_users(users)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    stocks = users[username].get('stocks', {})

    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        buy_price = float(request.form['purchase_price'])
        quantity = int(request.form['quantity'])
        alert_percentage = request.form.get('alert_percentage')

        global_symbols = load_stock_list_from_db()
        if symbol not in global_symbols:
            flash(f"{symbol} is not available in our global stock list.", "danger")
            return redirect(url_for('portfolio'))

        price_data = get_cached_prices([symbol])
        current_price = price_data.get(symbol, 'N/A')

        if symbol not in stocks:
            stocks[symbol] = {
                'buy_price': buy_price,
                'quantity': quantity,
                'current_price': current_price,
                'alert_percentage': float(alert_percentage) if alert_percentage else None
            }
        else:
            existing = stocks[symbol]
            total_qty = existing['quantity'] + quantity
            avg_price = (
                (existing['buy_price'] * existing['quantity']) +
                (buy_price * quantity)
            ) / total_qty
            stocks[symbol] = {
                'buy_price': round(avg_price, 2),
                'quantity': total_qty,
                'current_price': current_price,
                'alert_percentage': existing.get('alert_percentage') or
                                     (float(alert_percentage) if alert_percentage else None)
            }

        users[username]['stocks'] = stocks
        save_users(users)
        flash(f'Stock {symbol} added/updated successfully!', 'success')

    # Update prices and compute totals
    symbols = list(stocks.keys())
    updated_prices = get_cached_prices(symbols)
    total_value = 0
    daily_gain_loss = 0

    for symbol in symbols:
        stock = stocks[symbol]
        stock['current_price'] = updated_prices.get(symbol, 'N/A')
        try:
            curr = float(stock['current_price'])
            buy = float(stock['buy_price'])
            gain = (curr - buy) * stock['quantity']
            pct = ((curr - buy) / buy) * 100
            val = curr * stock['quantity']

            stock['value'] = round(val, 2)
            stock['percentage_change'] = round(pct, 2)
            total_value += val
            daily_gain_loss += gain

            # alert logic
            alert_msg = ''
            ap = stock.get('alert_percentage')
            if isinstance(ap, float):
                if pct >= ap:
                    alert_msg = f"Already gained {ap}%"
                elif pct <= -ap:
                    alert_msg = f"Already dropped {ap}%"
            stock['alert'] = alert_msg
        except:
            stock['value'] = stock['percentage_change'] = stock['alert'] = 'N/A'

    save_users(users)
    return render_template(
        'index.html',
        stocks=stocks,
        total_value=round(total_value, 2),
        daily_gain_loss=round(daily_gain_loss, 2)
    )

@app.route('/sell_stock', methods=['POST'])
def sell_stock():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    symbol = request.form['symbol'].upper()
    sell_qty = int(request.form['sell_quantity'])
    stocks = users[username].get('stocks', {})

    if symbol in stocks:
        if sell_qty >= stocks[symbol]['quantity']:
            del stocks[symbol]
        else:
            stocks[symbol]['quantity'] -= sell_qty
        save_users(users)
        flash(f'Sold {sell_qty} shares of {symbol}', 'success')
    else:
        flash(f'{symbol} not found in portfolio', 'danger')

    return redirect(url_for('portfolio'))

@app.route('/get_prices')
def get_prices():
    if 'username' not in session:
        return redirect(url_for('login'))

    symbols = list(users[session['username']]['stocks'].keys())
    updated = get_cached_prices(symbols)
    # update in-memory too
    for s, p in updated.items():
        users[session['username']]['stocks'][s]['current_price'] = p
    save_users(users)
    return jsonify(updated)

@app.route('/last_update_time')
def last_update_time():
    global last_price_update_time
    if last_price_update_time:
        est = timezone('US/Eastern')
        est_time = last_price_update_time.replace(tzinfo=utc).astimezone(est)
        market_open  = est_time.replace(hour=9,  minute=30, second=0, microsecond=0)
        market_close = est_time.replace(hour=16, minute=0,  second=0, microsecond=0)

        if est_time < market_open:
            minutes_left = 390
        elif est_time > market_close:
            minutes_left = 0
        else:
            minutes_left = int((market_close - est_time).total_seconds() / 60)

        return jsonify({
            "last_updated_est": est_time.strftime("%m/%d/%Y %I:%M:%S %p"),
            "minutes_left": minutes_left
        })

    return jsonify({"last_updated_est": "Never", "minutes_left": "N/A"})

@app.route('/stock_list')
def stock_list_route():
    symbols = load_stock_list_from_db()
    return render_template('stock_list.html', symbols=symbols)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    update_global_price_cache()
    app.run(host='0.0.0.0', port=5000, debug=True)
