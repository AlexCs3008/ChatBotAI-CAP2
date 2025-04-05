from datetime import datetime
from . import db

class BotCustomization(db.Model):
    __tablename__ = 'bot_customizations'
    
    id = db.Column(db.Integer, primary_key=True)
    storage_id = db.Column(db.String(100), unique=True, nullable=False)  # user_id or guest_id
    name = db.Column(db.String(100), nullable=False, default='Bot')
    character_id = db.Column(db.Integer, nullable=False, default=1)
    character_src = db.Column(db.String(255), nullable=False, default='/assets/characters/robo.gif')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)