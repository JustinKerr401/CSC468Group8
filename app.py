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

from datetime import datetime, timedelta

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = mongo.db.users.find_one({"email": request.form["email"]})
        if user and check_password_hash(user["password"], request.form["password"]):
            session["email"] = user["email"]

            # Get the user's stocks and check if any need updating
            email = session["email"]
            stocks = mongo.db.stocks.find({"email": email})

            thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)

            for stock in stocks:
                # If the stock hasn't been updated in the last 30 minutes, update it
                if stock["last_checked"] < thirty_minutes_ago:
                    current_price = get_stock_price(stock["symbol"])
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

    # Pass 'email' and 'stock_data' to the template
    return render_template("portfolio.html", email=email, stocks=stock_data)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
