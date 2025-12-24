import json
import os

DATA_FOLDER = "data"
DATA_FILE = os.path.join(DATA_FOLDER, "users.json")

os.makedirs(DATA_FOLDER, exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def ensure_user(data, user_id):
    if user_id not in data:
        data[user_id] = {
            "coins": 0,
            "inventory": []
        }

def get_user_coins(user_id):
    data = load_data()
    ensure_user(data, user_id)
    save_data(data)
    return data[user_id]["coins"]

def add_user_coins(user_id, amount):
    data = load_data()
    ensure_user(data, user_id)
    data[user_id]["coins"] += amount
    save_data(data)

def deduct_user_coins(user_id, amount):
    data = load_data()
    ensure_user(data, user_id)
    data[user_id]["coins"] = max(0, data[user_id]["coins"] - amount)
    save_data(data)

def add_item_to_inventory(user_id, item):
    data = load_data()
    ensure_user(data, user_id)
    data[user_id]["inventory"].append(item)
    save_data(data)
