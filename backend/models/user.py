# models/user.py
from app import db
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    
    # OAuth tokens (encrypted in production)
    notion_access_token = db.Column(db.Text)
    notion_refresh_token = db.Column(db.Text)
    google_access_token = db.Column(db.Text)
    google_refresh_token = db.Column(db.Text)
    
    # Subscription
    stripe_customer_id = db.Column(db.String(255))
    subscription_status = db.Column(db.String(50), default='free')
    plan_type = db.Column(db.String(50), default='free')
    subscription_end_date = db.Column(db.DateTime)
    
    # Security
    api_key = db.Column(db.String(255), unique=True)
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    syncs = db.relationship('Sync', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_api_key(self):
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key

    def can_create_sync(self):
        limits = {
            'free': 1,
            'starter': 3,
            'pro': 10,
            'business': -1  # unlimited
        }
        
        current_count = len(self.syncs)
        limit = limits.get(self.plan_type, 0)
        
        return limit == -1 or current_count < limit

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan_type': self.plan_type,
            'subscription_status': self.subscription_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# models/sync.py
class Sync(db.Model):
    __tablename__ = 'syncs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Sync configuration
    name = db.Column(db.String(255), nullable=False)
    notion_database_id = db.Column(db.String(255), nullable=False)
    sheet_id = db.Column(db.String(255), nullable=False)
    
    # Sync settings
    mapping = db.Column(db.JSON)  # Field mapping between Notion and Sheets
    filters = db.Column(db.JSON)  # Conditional filters
    frequency = db.Column(db.String(50), default='daily')  # realtime, hourly, daily, weekly
    sync_direction = db.Column(db.String(50), default='both')  # notion_to_sheets, sheets_to_notion, both
    
    # Status
    status = db.Column(db.String(50), default='active')  # active, paused, error
    last_sync = db.Column(db.DateTime)
    next_sync = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    logs = db.relationship('SyncLog', backref='sync', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'frequency': self.frequency,
            'sync_direction': self.sync_direction,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# models/log.py  
class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_id = db.Column(db.Integer, db.ForeignKey('syncs.id'), nullable=False)
    
    # Log details
    status = db.Column(db.String(50), nullable=False)  # started, completed, error
    message = db.Column(db.Text)
    rows_processed = db.Column(db.Integer, default=0)
    errors = db.Column(db.JSON)
    
    # Performance metrics
    duration_seconds = db.Column(db.Float)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'message': self.message,
            'rows_processed': self.rows_processed,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }