# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

from models.user import User
from models.sync import Sync
from models.log import SyncLog
from services.notion_service import NotionService
from services.sheets_service import SheetsService
from services.sync_engine import SyncEngine
from auth.oauth import OAuth

# Initialize services
notion_service = NotionService()
sheets_service = SheetsService()
sync_engine = SyncEngine(notion_service, sheets_service)
oauth = OAuth()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/auth/notion', methods=['POST'])
@jwt_required()
def auth_notion():
    user_id = get_jwt_identity()
    redirect_uri = request.json.get('redirect_uri')
    
    auth_url = oauth.get_notion_auth_url(user_id, redirect_uri)
    return jsonify({'auth_url': auth_url}), 200

@app.route('/auth/google', methods=['POST'])
@jwt_required()
def auth_google():
    user_id = get_jwt_identity()
    redirect_uri = request.json.get('redirect_uri')
    
    auth_url = oauth.get_google_auth_url(user_id, redirect_uri)
    return jsonify({'auth_url': auth_url}), 200

@app.route('/sync/create', methods=['POST'])
@jwt_required()
def create_sync():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate user can create sync based on plan
        user = User.query.get(user_id)
        if not user.can_create_sync():
            return jsonify({'error': 'Sync limit reached for your plan'}), 403
        
        sync = Sync(
            user_id=user_id,
            name=data.get('name'),
            notion_database_id=data.get('notion_database_id'),
            sheet_id=data.get('sheet_id'),
            mapping=data.get('mapping', {}),
            filters=data.get('filters', {}),
            frequency=data.get('frequency', 'daily'),
            sync_direction=data.get('sync_direction', 'both')
        )
        
        db.session.add(sync)
        db.session.commit()
        
        return jsonify({
            'id': sync.id,
            'message': 'Sync created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/sync/run/<int:sync_id>', methods=['POST'])
@jwt_required()
def run_sync(sync_id):
    try:
        user_id = get_jwt_identity()
        sync = Sync.query.filter_by(id=sync_id, user_id=user_id).first()
        
        if not sync:
            return jsonify({'error': 'Sync not found'}), 404
        
        result = sync_engine.run_sync(sync)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sync/<int:sync_id>/logs', methods=['GET'])
@jwt_required()
def get_sync_logs(sync_id):
    try:
        user_id = get_jwt_identity()
        sync = Sync.query.filter_by(id=sync_id, user_id=user_id).first()
        
        if not sync:
            return jsonify({'error': 'Sync not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        logs = SyncLog.query.filter_by(sync_id=sync_id)\
                           .order_by(SyncLog.created_at.desc())\
                           .paginate(page=page, per_page=20, error_out=False)
        
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_ENV') == 'development')