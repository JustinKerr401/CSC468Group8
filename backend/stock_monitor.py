from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_session import Session
import yfinance as yf
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

USERS_FILE = "users.json"

# Load users from JSON file
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save users to JSON file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

users = load_users()

# Fetch the real time prices from Yahoo Finance that will be displayed to users
def fetch_real_time_price(symbol):
    stock = yf.Ticker(symbol)
    try:
        todays_data = stock.history(period='1d')
        return todays_data['Close'][0]
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

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
            # Create a new user
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
        purchase_price = float(request.form['purchase_price'])
        alert_percentage = float(request.form['alert_percentage'])

        if symbol not in stocks:
            stocks[symbol] = {
                'purchase_price': purchase_price,
                'alert_percentage': alert_percentage,
                'current_price': fetch_real_time_price(symbol),
                'status': 'Monitoring'
            }
            users[username]['stocks'] = stocks
            save_users(users)
            flash(f'Stock {symbol} added successfully!', 'success')
        else:
            flash(f'Stock {symbol} already exists!', 'warning')

    return render_template('index.html', stocks=stocks)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
