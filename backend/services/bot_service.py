from datetime import datetime
from models import db
from models.bot_customization import BotCustomization

class BotService:
    @staticmethod
    def get_bot_customization(storage_id):
        customization = BotCustomization.query.filter_by(storage_id=storage_id).first()
        
        if not customization:
            return None
            
        return {
            'name': customization.name,
            'characterId': customization.character_id,
            'characterSrc': customization.character_src,
            'updated_at': customization.updated_at.isoformat()
        }
    
    @staticmethod
    def save_bot_customization(storage_id, name, character_id, character_src):
        customization = BotCustomization.query.filter_by(storage_id=storage_id).first()
        
        if not customization:
            customization = BotCustomization(
                storage_id=storage_id,
                name=name,
                character_id=character_id,
                character_src=character_src
            )
            db.session.add(customization)
        else:
            customization.name = name
            customization.character_id = character_id
            customization.character_src = character_src
            customization.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'name': customization.name,
            'characterId': customization.character_id,
            'characterSrc': customization.character_src,
            'updated_at': customization.updated_at.isoformat()
        }
    
    # Add to bot_service.py
@staticmethod
def transfer_customization(from_user_id, to_user_id):
    """Transfer bot customization from one user ID to another."""
    customization = BotCustomization.query.filter_by(user_id=from_user_id).first()
    
    if customization:
        # Check if destination user already has customization
        existing = BotCustomization.query.filter_by(user_id=to_user_id).first()
        
        if existing:
            # Update existing customization
            existing.name = customization.name
            existing.character_id = customization.character_id
            existing.character_src = customization.character_src
        else:
            # Create new customization
            new_custom = BotCustomization(
                user_id=to_user_id,
                name=customization.name,
                character_id=customization.character_id,
                character_src=customization.character_src
            )
            db.session.add(new_custom)
        
        db.session.commit()
        return True
    
    return False