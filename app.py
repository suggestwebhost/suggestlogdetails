from flask import Flask, request, jsonify
from datetime import datetime, timezone
# (Include your existing pymongo setup/db initialization here)

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
