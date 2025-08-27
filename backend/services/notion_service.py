# services/notion_service.py
import requests
import logging
from typing import Dict, List, Optional

class NotionService:
    def __init__(self):
        self.base_url = 'https://api.notion.com/v1'
        self.logger = logging.getLogger(__name__)

    def get_database_rows(self, database_id: str, access_token: str, filters: Dict = None) -> List[Dict]:
        """Fetch all rows from a Notion database"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            url = f'{self.base_url}/databases/{database_id}/query'
            
            payload = {}
            if filters:
                payload['filter'] = self._build_notion_filter(filters)
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # Handle pagination
            while data.get('has_more', False):
                payload['start_cursor'] = data.get('next_cursor')
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                results.extend(data.get('results', []))
            
            return results
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch Notion database rows: {str(e)}")
            raise

    def get_page(self, page_id: str, access_token: str) -> Optional[Dict]:
        """Fetch a specific Notion page"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            url = f'{self.base_url}/pages/{page_id}'
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch Notion page {page_id}: {str(e)}")
            return None

    def update_database_rows(self, database_id: str, data: List[Dict], access_token: str):
        """Update or create rows in Notion database"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            for row in data:
                # Check if row exists (by unique identifier)
                existing_page = self._find_existing_page(database_id, row, access_token)
                
                if existing_page:
                    # Update existing page
                    self._update_page(existing_page['id'], row, access_token)
                else:
                    # Create new page
                    self._create_page(database_id, row, access_token)
                    
        except Exception as e:
            self.logger.error(f"Failed to update Notion database: {str(e)}")
            raise

    def _create_page(self, database_id: str, row_data: Dict, access_token: str):
        """Create a new page in Notion database"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        
        url = f'{self.base_url}/pages'
        
        payload = {
            'parent': {'database_id': database_id},
            'properties': self._format_properties_for_notion(row_data)
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

    def _update_page(self, page_id: str, row_data: Dict, access_token: str):
        """Update an existing Notion page"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        
        url = f'{self.base_url}/pages/{page_id}'
        
        payload = {
            'properties': self._format_properties_for_notion(row_data)
        }
        
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()

    def _format_properties_for_notion(self, row_data: Dict) -> Dict:
        """Format row data for Notion API"""
        properties = {}
        
        for field_name, value in row_data.items():
            if isinstance(value, str):
                properties[field_name] = {
                    'rich_text': [{'text': {'content': value}}]
                }
            elif isinstance(value, (int, float)):
                properties[field_name] = {
                    'number': value
                }
            # Add more type handling as needed
        
        return properties

    def _build_notion_filter(self, filters: Dict) -> Dict:
        """Build Notion API filter from simple filter dict"""
        notion_filters = []
        
        for field, condition in filters.items():
            filter_obj = {
                'property': field,
                'rich_text': {
                    condition.get('operator', 'contains'): condition.get('value', '')
                }
            }
            notion_filters.append(filter_obj)
        
        if len(notion_filters) == 1:
            return notion_filters[0]
        else:
            return {'and': notion_filters}

    def get_database_schema(self, database_id: str, access_token: str) -> Dict:
        """Get database schema for field mapping"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Notion-Version': '2022-06-28'
            }
            
            url = f'{self.base_url}/databases/{database_id}'
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch database schema: {str(e)}")
            raise