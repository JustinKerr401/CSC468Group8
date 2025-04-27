from pymongo import MongoClient
import json
import os

json_path = os.path.join(os.path.dirname(__file__), "..", "stock_list.json")


# Connect to MongoDB container
client = MongoClient("mongodb://mongo:27017/")
db = client.stock_tracker
stock_list = db.stock_list

# Load JSON data
with open(json_path, "r") as f:
    stock_data = json.load(f)

# Clear old entries
stock_list.delete_many({})

# Insert new data
result = stock_list.insert_many(stock_data)
print(f"✅ Inserted {len(result.inserted_ids)} stocks into MongoDB.")
