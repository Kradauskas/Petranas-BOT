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
    # Write to a temp file first so a crash mid-write can't wipe everyone's coins
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)

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


def get_user_field(user_id, field, default=None):
    data = load_data()
    return data.get(user_id, {}).get(field, default)

def set_user_field(user_id, field, value):
    data = load_data()
    ensure_user(data, user_id)
    data[user_id][field] = value
    save_data(data)

def top_users(limit=10):
    data = load_data()
    ranked = sorted(data.items(), key=lambda kv: kv[1].get("coins", 0), reverse=True)
    return [(uid, info.get("coins", 0)) for uid, info in ranked[:limit]]
