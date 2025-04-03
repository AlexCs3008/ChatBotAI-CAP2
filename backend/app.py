import os
import logging
import uuid
import hashlib
import json
from datetime import datetime, timedelta
import jwt
from flask import Flask, request, jsonify, session
import openai
from dotenv import load_dotenv
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {'Yes' if OPENAI_API_KEY else 'No'}")

# Initialize OpenAI client with the updated SDK approach
openai.api_key = OPENAI_API_KEY

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))  # Needed for session
JWT_SECRET = os.getenv("JWT_SECRET", os.urandom(24).hex())
CORS(app, origins=["http://localhost:8000"], supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Default system message to instruct the AI
DEFAULT_SYSTEM_MESSAGE = """
You are a helpful assistant. Provide concise, accurate responses to user questions.
Respond in a friendly and helpful manner.
"""

# Mock database for users (in production, use a real database)
users_db = {}  # userid -> user data
bot_customizations = {}  # userid -> bot customization
conversation_histories = {} #Keep track of conversations

# Helper functions for authentication
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    
    return salt, hash_obj.hex()

def verify_password(password, stored_salt, stored_hash):
    _, new_hash = hash_password(password, stored_salt)
    return new_hash == stored_hash

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_auth_user_id(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    return verify_token(token)

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email', '').lower()
        password = data.get('password')
        
        # Validation
        if not all([name, email, password]):
            return jsonify({"error": "Name, email, and password are required"}), 400
        
        # Check if email already exists
        for user in users_db.values():
            if user.get('email') == email:
                return jsonify({"error": "Email already registered"}), 409
        
        # Create user
        user_id = str(uuid.uuid4())
        salt, hashed_password = hash_password(password)
        
        users_db[user_id] = {
            'id': user_id,
            'name': name,
            'email': email,
            'password_salt': salt,
            'password_hash': hashed_password,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Generate token
        token = generate_token(user_id)
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'name': name,
                'email': email
            }
        })
        
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred during registration"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email', '').lower()
        password = data.get('password')
        
        # Validation
        if not all([email, password]):
            return jsonify({"error": "Email and password are required"}), 400
        
        # Find user by email
        user_id = None
        user = None
        
        for uid, u in users_db.items():
            if u.get('email') == email:
                user_id = uid
                user = u
                break
        
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Verify password
        if not verify_password(password, user['password_salt'], user['password_hash']):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Generate token
        token = generate_token(user_id)
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred during login"}), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        user_id = get_auth_user_id(request)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        user = users_db[user_id]
        
        return jsonify({
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_user endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred retrieving user data"}), 500

@app.route('/api/user', methods=['PUT'])
def update_user():
    try:
        user_id = get_auth_user_id(request)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        data = request.json
        
        # Only allow updating name and email
        if 'name' in data:
            users_db[user_id]['name'] = data['name']
        
        if 'email' in data:
            # Check if email is unique
            new_email = data['email'].lower()
            for uid, user in users_db.items():
                if uid != user_id and user.get('email') == new_email:
                    return jsonify({"error": "Email already in use"}), 409
            
            users_db[user_id]['email'] = new_email
        
        logger.info(f"User updated: {user_id}")
        
        return jsonify({
            'user': {
                'id': user_id,
                'name': users_db[user_id]['name'],
                'email': users_db[user_id]['email']
            }
        })
        
    except Exception as e:
        logger.error(f"Error in update_user endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred updating user data"}), 500

@app.route('/api/password', methods=['PUT'])
def change_password():
    try:
        user_id = get_auth_user_id(request)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        data = request.json
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not all([current_password, new_password]):
            return jsonify({"error": "Current and new passwords are required"}), 400
        
        # Verify current password
        if not verify_password(current_password, users_db[user_id]['password_salt'], users_db[user_id]['password_hash']):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update password
        salt, hashed_password = hash_password(new_password)
        users_db[user_id]['password_salt'] = salt
        users_db[user_id]['password_hash'] = hashed_password
        
        logger.info(f"Password changed for user: {user_id}")
        
        return jsonify({"message": "Password updated successfully"})
        
    except Exception as e:
        logger.error(f"Error in change_password endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred changing password"}), 500

# Bot customization routes
@app.route('/api/bot-customization', methods=['POST'])
def save_bot_customization():
    try:
        data = request.json
        user_id = get_auth_user_id(request)
        guest_id = data.get('guest_id')
        
        if not user_id and not guest_id:
            return jsonify({"error": "Authentication or guest ID required"}), 401
        
        storage_id = user_id if user_id else f"guest_{guest_id}"
        
        bot_customizations[storage_id] = {
            'name': data.get('name', 'Bot'),
            'characterId': data.get('characterId', 1),
            'characterSrc': data.get('characterSrc', '/assets/characters/robo.gif'),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Bot customization saved for {'user' if user_id else 'guest'}: {storage_id}")
        
        return jsonify({
            'customization': bot_customizations[storage_id]
        })
        
    except Exception as e:
        logger.error(f"Error in save_bot_customization endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred saving bot customization"}), 500

@app.route('/api/bot-customization', methods=['GET'])
def get_bot_customization():
    try:
        user_id = get_auth_user_id(request)
        guest_id = request.args.get('guest_id')
        
        if not user_id and not guest_id:
            return jsonify({"error": "Authentication or guest ID required"}), 401
        
        storage_id = user_id if user_id else f"guest_{guest_id}"
        
        if storage_id not in bot_customizations:
            return jsonify({"customization": None})
        
        return jsonify({
            'customization': bot_customizations[storage_id]
        })
        
    except Exception as e:
        logger.error(f"Error in get_bot_customization endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred retrieving bot customization"}), 500


# Chat routes (updated)
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Get the user's message from request
        data = request.json
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")
       
        # Get bot customization if available
        user_id = get_auth_user_id(request)
        guest_id = data.get("guest_id")
       
        # Personalize system message if bot is customized
        system_message = DEFAULT_SYSTEM_MESSAGE
       
        if user_id or guest_id:
            storage_id = user_id if user_id else f"guest_{guest_id}"
            if storage_id in bot_customizations:
                bot_name = bot_customizations[storage_id].get('name', 'Bot')
                system_message = f"""
                You are {bot_name}, a helpful assistant. Provide concise, accurate responses to user questions.
                Respond in a friendly and helpful manner. Always sign your responses as {bot_name}.
                """
       
        # Validate input
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
       
        # Get or initialize conversation history
        global conversation_histories
        if session_id not in conversation_histories:
            conversation_histories[session_id] = [
                {"role": "system", "content": system_message}
            ]
        
        conversation_history = conversation_histories[session_id]
       
        # Update system message if it changed
        if conversation_history[0]["content"] != system_message:
            conversation_history[0]["content"] = system_message
       
        # Add user message to history
        conversation_history.append({"role": "user", "content": user_message})
       
        # Log the incoming message
        logger.info(f"User message: {user_message[:50]}..." if len(user_message) > 50 else f"User message: {user_message}")
        
        # For very long conversations, truncate for API call
        api_messages = conversation_history
        if len(api_messages) > 50:  # Adjust based on your token limit needs
            # Keep system message and last 49 messages for API call
            api_messages = [conversation_history[0]] + conversation_history[-49:]
       
        # Call the OpenAI API with conversation history for context
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=api_messages,  # Use the potentially truncated messages for API
            temperature=0.7
        )
       
        # Extract the assistant's message
        assistant_message = response.choices[0].message.content
       
        # Add assistant response to conversation history
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        # Save updated history back to the global dictionary
        conversation_histories[session_id] = conversation_history
       
        # Log the assistant's response
        logger.info(f"Assistant response: {assistant_message[:50]}..." if len(assistant_message) > 50 else f"Assistant response: {assistant_message}")
       
        # Get bot customization data for response
        bot_data = None
        if user_id or guest_id:
            storage_id = user_id if user_id else f"guest_{guest_id}"
            if storage_id in bot_customizations:
                bot_data = bot_customizations[storage_id]
       
        return jsonify({
            "reply": assistant_message,
            "session_id": session_id,
            "bot": bot_data
        })
       
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    try:
        data = request.json
        session_id = data.get("session_id", "default")
        
        # Get bot customization if available
        user_id = get_auth_user_id(request)
        guest_id = data.get("guest_id")
        
        # Personalize system message if bot is customized
        system_message = DEFAULT_SYSTEM_MESSAGE
        
        if user_id or guest_id:
            storage_id = user_id if user_id else f"guest_{guest_id}"
            if storage_id in bot_customizations:
                bot_name = bot_customizations[storage_id].get('name', 'Bot')
                system_message = f"""
                You are {bot_name}, a helpful assistant. Provide concise, accurate responses to user questions.
                Respond in a friendly and helpful manner. Always sign your responses as {bot_name}.
                """
        
        # Reset the conversation history with the customized system message
        session[session_id] = [{"role": "system", "content": system_message}]
        
        return jsonify({"status": "success", "message": "Conversation has been reset"})
        
    except Exception as e:
        logger.error(f"Error in reset_chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while resetting the conversation"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting server on port {port}, debug mode: {debug_mode}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)