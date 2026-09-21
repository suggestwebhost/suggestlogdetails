from flask import Flask, request, jsonify
from datetime import datetime, timezone
# (Include your existing pymongo setup/db initialization here)
import os
from flask import Flask, request, jsonify
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

app = Flask(__name__)

# Replace this with your actual MongoDB Atlas connection string from your cloud console
# Example format: mongodb+srv://<username>:<password>@cluster0.xxxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_URI = os.getenv("MONGO_URI")

try:
    # Initialize MongoDB Client
    client = MongoClient(MONGO_URI)
    # Define/select Database Name
    db = client['auth_service_db']
    # Define/select Collection Name (equivalent to a table)
    users_collection = db['users']
    
    # Simple check to see if connection works
    client.admin.command('ping')
    print("Successfully connected to MongoDB Cloud!")
except (ConnectionFailure, Exception) as e:
    print(f"Could not connect to MongoDB. Error: {e}")


@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Check if user exists
    if db.users.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 400
        
    # Insert new user with default status fields
    new_user = {
        "username": username,
        "password": password, # Note: In production, hash this with bcrypt!
        "is_online": False,
        "last_login": None,
        "last_logout": None
    }
    db.users.insert_one(new_user)
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = db.users.find_one({"username": username, "password": password})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Update login timestamp and set online status to True
    current_time = datetime.now(timezone.utc).isoformat()
    db.users.update_one(
        {"username": username},
        {"$set": {"is_online": True, "last_login": current_time}}
    )
    return jsonify({"message": f"Welcome back, {username}!"}), 200

@app.route('/logout', methods=['POST'])
def logout_user():
    data = request.get_json()
    username = data.get('username')
    
    # Update logout timestamp and set online status to False
    current_time = datetime.now(timezone.utc).isoformat()
    db.users.update_one(
        {"username": username},
        {"$set": {"is_online": False, "last_logout": current_time}}
    )
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/users/status', methods=['GET'])
def get_users_status():
    # Fetch all users from MongoDB, excluding their passwords for security
    users_cursor = db.users.find({}, {"_add": 0, "password": 0})
    
    user_list = []
    for user in users_cursor:
        user_list.append({
            "username": user.get("username"),
            "is_online": user.get("is_online", False),
            "last_login": user.get("last_login"),
            "last_logout": user.get("last_logout")
        })
        
    return jsonify({"users": user_list}), 200
