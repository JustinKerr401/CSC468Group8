from flask import Flask, render_template, request, redirect, session, url_for, make_response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import io
import yfinance as yf

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

app.config["MONGO_URI"] = "mongodb://mongo:27017/stockapp"
mongo = PyMongo(app)

def fetch_real_time_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        todays_data = stock.history(period='1d')
        return float(todays_data['Close'][0])
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = mongo.db.users.find_one({"email": request.form["email"]})
        if user and check_password_hash(user["password"], request.form["password"]):
            session["email"] = user["email"]

            email = session["email"]
            stocks = mongo.db.stocks.find({"email": email})
            thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)

            for stock in stocks:
                if stock["last_checked"] < thirty_minutes_ago:
                    current_price = fetch_real_time_price(stock["symbol"])
                    if current_price is not None:
                        mongo.db.stocks.update_one(
                            {"_id": stock["_id"]},
                            {"$set": {
                                "current_price": current_price,
                                "last_checked": datetime.utcnow()
                            }}
                        )

            return redirect("/portfolio")
        return render_template("login.html", error="Invalid credentials.")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        if mongo.db.users.find_one({"email": email}):
            return render_template("signup.html", error="User already exists.")
        mongo.db.users.insert_one({"email": email, "password": password})
        return redirect("/")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    if "email" not in session:
        return redirect("/")

    email = session["email"]

    if request.method == "POST":
        symbol = request.form["symbol"].upper()
        purchase_price = float(request.form["purchase_price"])
        alert_percentage = float(request.form["alert_percentage"])
        current_price = fetch_real_time_price(symbol)
        timestamp = datetime.utcnow()

        mongo.db.stocks.insert_one({
            "email": email,
            "symbol": symbol,
            "purchase_price": purchase_price,
            "alert_percentage": alert_percentage,
            "current_price": current_price,
            "last_checked": timestamp
        })

    stocks = mongo.db.stocks.find({"email": email})
    stock_data = {}
    for stock in stocks:
        status = "OK"
        if stock["current_price"]:
            change = abs((stock["current_price"] - stock["purchase_price"]) / stock["purchase_price"]) * 100
            if change >= stock["alert_percentage"]:
                status = "ALERT"
        if stock["symbol"] not in stock_data:
            stock_data[stock["symbol"]] = []
        stock_data[stock["symbol"]].append({
            "purchase_price": stock["purchase_price"],
            "current_price": stock.get("current_price", "N/A"),
            "alert_percentage": stock["alert_percentage"],
            "status": status,
            "last_checked": stock["last_checked"]
        })

    return render_template("portfolio.html", email=email, stocks=stock_data)

@app.route("/download_pdf")
def download_pdf():
    if "email" not in session:
        return redirect("/")

    email = session["email"]
    stocks = mongo.db.stocks.find({"email": email})

    response = make_response(generate_pdf(email, stocks))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=portfolio.pdf"
    
    return response

def generate_pdf(email, stocks):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.drawString(100, 750, f"Portfolio for {email}")
    y_position = 730
    y_position -= 20

    for stock in stocks:
        c.drawString(100, y_position, f"Symbol: {stock['symbol']}")
        y_position -= 20

        c.drawString(100, y_position, f"Purchase Price: ${stock['purchase_price']}")
        y_position -= 20

        c.drawString(100, y_position, f"Current Price: ${stock.get('current_price', 'N/A')}")
        y_position -= 20

        c.drawString(100, y_position, f"Alert Percentage: {stock['alert_percentage']}%")
        y_position -= 20

        c.drawString(100, y_position, f"Status: {stock.get('status', 'N/A')}")
        y_position -= 20

        c.drawString(100, y_position, f"Last Checked: {stock['last_checked']}")
        y_position -= 40

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
