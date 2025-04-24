from flask import Flask, render_template, request, redirect, session, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from stock_api import get_stock_price
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

app.config["MONGO_URI"] = "mongodb://mongo:27017/stockapp"
mongo = PyMongo(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = mongo.db.users.find_one({"email": request.form["email"]})
        if user and check_password_hash(user["password"], request.form["password"]):
            session["email"] = user["email"]
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
        current_price = get_stock_price(symbol)
        timestamp = datetime.utcnow()

        mongo.db.stocks.insert_one({
            "email": email,
            "symbol": symbol,
            "purchase_price": purchase_price,
            "alert_percentage": alert_percentage,
            "current_price": current_price,
            "last_checked": timestamp
        })

    # Find all stocks for the user, regardless of symbol
    stocks = mongo.db.stocks.find({"email": email})
    stock_data = {}

    for stock in stocks:
        # Ensure that each symbol gets its own list of stocks
        if stock["symbol"] not in stock_data:
            stock_data[stock["symbol"]] = []

        status = "OK"
        if stock["current_price"]:
            change = abs((stock["current_price"] - stock["purchase_price"]) / stock["purchase_price"]) * 100
            if change >= stock["alert_percentage"]:
                status = "ALERT"

        stock_data[stock["symbol"]].append({
            "purchase_price": stock["purchase_price"],
            "current_price": stock.get("current_price", "N/A"),
            "alert_percentage": stock["alert_percentage"],
            "status": status,
            "last_checked": stock["last_checked"]
        })

    return render_template("portfolio.html", stocks=stock_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
