import json
import openai
from datetime import datetime
from models import db
from models.conversation import Conversation
from models.message import Message

class ChatService:
    @staticmethod
    def get_or_create_conversation(user_id, session_id):
        """Get or create a conversation."""
        conversation = Conversation.query.filter_by(session_id=session_id).first()
        
        if not conversation:
            # Create a new conversation
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                title=f"New conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.session.add(conversation)
            db.session.commit()
            
        return conversation
    
    @staticmethod
    def add_message(conversation_id, role, content):
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        # Update the conversation's updated_at timestamp
        conversation = Conversation.query.get(conversation_id)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return message
    
    @staticmethod
    def get_chat_history(user_id, session_id):
        """Retrieve chat history for a specific session."""
        conversation = Conversation.query.filter_by(session_id=session_id).first()
        
        if not conversation:
            return []
            
        # Only return user and assistant messages (not system messages)
        messages = Message.query.filter_by(
            conversation_id=conversation.id
        ).filter(
            Message.role.in_(['user', 'assistant'])
        ).order_by(Message.timestamp).all()
        
        return [message.to_dict() for message in messages]
    
    @staticmethod
    def get_user_sessions(user_id):
        """Get all chat sessions for a user."""
        conversations = Conversation.query.filter_by(
            user_id=user_id
        ).order_by(Conversation.updated_at.desc()).all()
        
        return [conversation.to_dict() for conversation in conversations]
    
    @staticmethod
    def get_chat_response(user_id, session_id, user_message, system_message=None):
        """Get a response from the chatbot for a user message."""
        # Get or create conversation
        conversation = ChatService.get_or_create_conversation(user_id, session_id)
    
        # Update system message if provided
        if system_message:
            # Check if a system message already exists
            existing_system = Message.query.filter_by(
                conversation_id=conversation.id,
                role='system'
            ).first()
        
            if existing_system:
                existing_system.content = system_message
                db.session.commit()
            else:
                ChatService.add_message(conversation.id, 'system', system_message)
    
        # Add user message
        ChatService.add_message(conversation.id, 'user', user_message)
    
        # Gather all messages for the API request
        messages = []
    
        # First add system message if exists
        system_msg = Message.query.filter_by(
            conversation_id=conversation.id,
            role='system'
        ).first()
    
        if system_msg:
            messages.append({"role": "system", "content": system_msg.content})
    
        # Add all user and assistant messages
        conversation_messages = Message.query.filter_by(
            conversation_id=conversation.id
        ).filter(
            Message.role.in_(['user', 'assistant'])
        ).order_by(Message.timestamp).all()
    
        for msg in conversation_messages:
            messages.append({"role": msg.role, "content": msg.content})
    
        # Generate response using OpenAI v0.28.0 syntax
        import openai  # Use the module-level import
    
        response = openai.ChatCompletion.create(  # Note: ChatCompletion, not chat.completions
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
    
        # In v0.28.0, the response structure is different
        assistant_response = response['choices'][0]['message']['content'].strip()
    
        # Save assistant response
        ChatService.add_message(conversation.id, 'assistant', assistant_response)
    
        # Update conversation title if it's the first exchange
        if len(conversation_messages) <= 2 and not conversation.title.startswith("New conversation"):
            # Use the first part of the first user message as the title
            title_text = user_message[:30] + "..." if len(user_message) > 30 else user_message
            conversation.title = title_text
            db.session.commit()
    
        return assistant_response

    
    @staticmethod
    def reset_conversation(user_id, session_id, system_message=None):
        """Reset a conversation, keeping only the system message."""
        conversation = Conversation.query.filter_by(session_id=session_id).first()
        
        if conversation:
            # Delete all messages except system messages
            Message.query.filter_by(
                conversation_id=conversation.id
            ).filter(
                Message.role != 'system'
            ).delete()
            
            # Update system message if provided
            if system_message:
                system_msg = Message.query.filter_by(
                    conversation_id=conversation.id,
                    role='system'
                ).first()
                
                if system_msg:
                    system_msg.content = system_message
                else:
                    ChatService.add_message(conversation.id, 'system', system_message)
            
            # Reset conversation title
            conversation.title = f"New conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
        
        return True
        
    @staticmethod
    def transfer_conversations(from_user_id, to_user_id):
        """Transfer conversations from one user ID to another."""
        conversations = Conversation.query.filter_by(user_id=from_user_id).all()
        
        for conv in conversations:
            conv.user_id = to_user_id
        
        db.session.commit()
        return True