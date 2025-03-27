from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_session import Session
import yfinance as yf
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Connect to MongoDB
client = MongoClient("mongodb://db:27017/")
db = client.trading_db
users_collection = db.users

# Fetch users from MongoDB
def load_users():
    users = users_collection.find()
    return {user['username']: user for user in users}

# Save users to MongoDB
def save_users(users):
    for username, user_data in users.items():
        users_collection.update_one(
            {'username': username},
            {'$set': user_data},
            upsert=True
        )

# Load users initially
users = load_users()

# Fetch the real-time price from Yahoo Finance
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
    if 'username' in session:  # If the user is already logged in, redirect to portfolio
        return redirect(url_for('portfolio'))

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
            new_user = {'username': username, 'password': password, 'stocks': {}}
            users[username] = new_user
            save_users({username: new_user})
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if 'username' not in session:  # Redirect to login page if not logged in
        return redirect(url_for('login'))

    username = session['username']
    stocks = users[username].get('stocks', {})

    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        purchase_price = float(request.form['purchase_price'])
        alert_percentage = float(request.form['alert_percentage'])

        # Check if stock is already in portfolio
        if symbol not in stocks:
            stocks[symbol] = {
                'purchase_price': purchase_price,
                'alert_percentage': alert_percentage,
                'current_price': fetch_real_time_price(symbol),
                'status': 'Monitoring'
            }
            users[username]['stocks'] = stocks
            save_users({username: users[username]})
            flash(f'Stock {symbol} added successfully!', 'success')
        else:
            flash(f'Stock {symbol} already exists in your portfolio!', 'warning')

    return render_template('index.html', stocks=stocks)

@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the session
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
