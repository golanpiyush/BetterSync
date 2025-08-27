# auth/oauth.py
import os
import secrets
from urllib.parse import urlencode
import requests
from flask import current_app

class OAuth:
    def __init__(self):
        self.notion_client_id = os.getenv('NOTION_CLIENT_ID')
        self.notion_client_secret = os.getenv('NOTION_CLIENT_SECRET')
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    def get_notion_auth_url(self, user_id: str, redirect_uri: str) -> str:
        """Generate Notion OAuth URL"""
        state = secrets.token_urlsafe(32)
        
        # Store state with user_id for verification (use Redis in production)
        current_app.config['oauth_states'] = current_app.config.get('oauth_states', {})
        current_app.config['oauth_states'][state] = user_id
        
        params = {
            'client_id': self.notion_client_id,
            'response_type': 'code',
            'owner': 'user',
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        return f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"

    def get_google_auth_url(self, user_id: str, redirect_uri: str) -> str:
        """Generate Google OAuth URL"""
        state = secrets.token_urlsafe(32)
        
        # Store state with user_id for verification
        current_app.config['oauth_states'] = current_app.config.get('oauth_states', {})
        current_app.config['oauth_states'][state] = user_id
        
        params = {
            'client_id': self.google_client_id,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/spreadsheets',
            'redirect_uri': redirect_uri,
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    def exchange_notion_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange Notion authorization code for access token"""
        url = "https://api.notion.com/v1/oauth/token"
        
        auth = (self.notion_client_id, self.notion_client_secret)
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        response = requests.post(url, data=data, auth=auth)
        response.raise_for_status()
        
        return response.json()

    def exchange_google_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange Google authorization code for access token"""
        url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': self.google_client_id,
            'client_secret': self.google_client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        return response.json()