import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, session
import openai
from dotenv import load_dotenv
from flask_cors import CORS

# Import our database models and services
from models import db, init_db
from models.user import User
from models.bot_customization import BotCustomization
from models.conversation import Conversation
from services.auth_service import AuthService
from services.bot_service import BotService
from services.chat_service import ChatService
from utils.password_utils import hash_password, verify_password

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {'Yes' if OPENAI_API_KEY else 'No'}")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))  # Needed for session
JWT_SECRET = os.getenv("JWT_SECRET", os.urandom(24).hex())

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgre:XTkCGDFj3kf5K0bHFvLaE9c7NScesG1S@dpg-cvng81je5dus73dvvhfg-a.oregon-postgres.render.com/chatbot_4sdk"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize CORS
CORS(app, origins=["http://localhost:8000"], supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Initialize database
init_db(app)

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# Default system message to instruct the AI
DEFAULT_SYSTEM_MESSAGE = """
You are a helpful assistant. Provide concise, accurate responses to user questions.
Respond in a friendly and helpful manner.
"""

# Helper function for authentication
def get_auth_user_id(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    return AuthService.verify_token(token)

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
        
        # Call the service to handle registration
        result, error = AuthService.register(name, email, password)
        
        if error:
            return jsonify({"error": error}), 409
            
        logger.info(f"New user registered: {email}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred during registration"}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        user_id = get_auth_user_id(request)
        guest_id = request.args.get('guest_id')
        
        if not user_id and not guest_id:
            return jsonify({"error": "Authentication or guest ID required"}), 401
        
        storage_id = user_id if user_id else f"guest_{guest_id}"
        
        # Get sessions from service
        sessions = ChatService.get_user_sessions(storage_id)
        
        return jsonify(sessions)
        
    except Exception as e:
        logger.error(f"Error in get_sessions endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred retrieving sessions"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email', '').lower()
        password = data.get('password')
        
        # Validation
        if not all([email, password]):
            return jsonify({"error": "Email and password are required"}), 400
        
        # Call the service to handle login
        result, error = AuthService.login(email, password)
        
        if error:
            return jsonify({"error": error}), 401
            
        logger.info(f"User logged in: {email}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred during login"}), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        user_id = get_auth_user_id(request)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
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
        
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.json
        
        # Only allow updating name and email
        if 'name' in data:
            user.name = data['name']
        
        if 'email' in data:
            # Check if email is unique
            new_email = data['email'].lower()
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({"error": "Email already in use"}), 409
            
            user.email = new_email
        
        db.session.commit()
        logger.info(f"User updated: {user_id}")
        
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in update_user endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred updating user data"}), 500

@app.route('/api/password', methods=['PUT'])
def change_password():
    try:
        user_id = get_auth_user_id(request)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.json
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not all([current_password, new_password]):
            return jsonify({"error": "Current and new passwords are required"}), 400
        
        # Verify current password
        if not verify_password(current_password, user.password_salt, user.password_hash):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update password
        salt, hashed_password = hash_password(new_password)
        user.password_salt = salt
        user.password_hash = hashed_password
        
        db.session.commit()
        logger.info(f"Password changed for user: {user_id}")
        
        return jsonify({"message": "Password updated successfully"})
        
    except Exception as e:
        db.session.rollback()
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
        
        name = data.get('name', 'Bot')
        character_id = data.get('characterId', 1)
        character_src = data.get('characterSrc', '/assets/characters/robo.gif')
        
        customization = BotService.save_bot_customization(
            storage_id, 
            name, 
            character_id, 
            character_src
        )
        
        logger.info(f"Bot customization saved for {'user' if user_id else 'guest'}: {storage_id}")
        
        return jsonify({
            'customization': customization
        })
        
    except Exception as e:
        db.session.rollback()
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
        
        customization = BotService.get_bot_customization(storage_id)
        
        return jsonify({
            'customization': customization
        })
        
    except Exception as e:
        logger.error(f"Error in get_bot_customization endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred retrieving bot customization"}), 500

# Chat routes (updated)
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Get the user's message from request
        data = request.json
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")
       
        # Get user ID (authenticated or guest)
        user_id = get_auth_user_id(request)
        guest_id = data.get("guest_id")
        storage_id = user_id if user_id else f"guest_{guest_id}"
       
        # Personalize system message if bot is customized
        system_message = DEFAULT_SYSTEM_MESSAGE
       
        if storage_id:
            customization = BotService.get_bot_customization(storage_id)
            if customization:
                bot_name = customization.get('name', 'Bot')
                system_message = f"""
                You are {bot_name}, a helpful assistant. Provide concise, accurate responses to user questions.
                Respond in a friendly and helpful manner. Always sign your responses as {bot_name}.
                """
       
        # Validate input
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get chat response using service
        assistant_message = ChatService.get_chat_response(
            storage_id, 
            session_id, 
            user_message, 
            system_message
        )
        
        # Log the messages
        logger.info(f"User message: {user_message[:50]}..." if len(user_message) > 50 else f"User message: {user_message}")
        logger.info(f"Assistant response: {assistant_message[:50]}..." if len(assistant_message) > 50 else f"Assistant response: {assistant_message}")
       
        # Get bot customization data for response
        bot_data = None
        if storage_id:
            bot_data = BotService.get_bot_customization(storage_id)
       
        return jsonify({
            "reply": assistant_message,
            "session_id": session_id,
            "bot": bot_data
        })
       
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred processing your request"}), 500


# Add the chat history endpoint
@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    try:
        session_id = request.args.get('session_id')
        user_id = get_auth_user_id(request)
        guest_id = request.args.get('guest_id')
        
        if not session_id:
            return jsonify({"error": "Session ID required"}), 400
            
        # Determine storage ID (authenticated user or guest)
        storage_id = user_id if user_id else f"guest_{guest_id}"
        
        # Get messages using service
        messages = ChatService.get_chat_history(storage_id, session_id)
        
        return jsonify({
            "session_id": session_id,
            "messages": messages
        })
        
    except Exception as e:
        logger.error(f"Error in get_chat_history endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred retrieving chat history"}), 500

@app.route('/api/reset-chat', methods=['POST'])
def reset_chat():
    try:
        data = request.json
        session_id = data.get("session_id", "default")
        
        # Get user ID (authenticated or guest)
        user_id = get_auth_user_id(request)
        guest_id = data.get("guest_id")
        storage_id = user_id if user_id else f"guest_{guest_id}"
        
        # Personalize system message if bot is customized
        system_message = DEFAULT_SYSTEM_MESSAGE
        
        if storage_id:
            customization = BotService.get_bot_customization(storage_id)
            if customization:
                bot_name = customization.get('name', 'Bot')
                system_message = f"""
                You are {bot_name}, a helpful assistant. Provide concise, accurate responses to user questions.
                Respond in a friendly and helpful manner. Always sign your responses as {bot_name}.
                """
        
        # Reset the conversation using service
        ChatService.reset_conversation(storage_id, session_id, system_message)
        
        return jsonify({"status": "success", "message": "Conversation has been reset"})
        
    except Exception as e:
        logger.error(f"Error in reset_chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while resetting the conversation"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        user_id = get_auth_user_id(request)
        if user_id:
            # You could implement token invalidation here
            # For example, add token to a blacklist or update last_logout timestamp
            pass
            
        return jsonify({"message": "Logged out successfully"})
        
    except Exception as e:
        logger.error(f"Error in logout endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred during logout"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting server on port {port}, debug mode: {debug_mode}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)