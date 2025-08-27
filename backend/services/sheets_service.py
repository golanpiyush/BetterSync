# services/sheets_service.py
import json
import logging
from typing import Dict, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class SheetsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_sheet_data(self, sheet_id: str, access_token: str, range_name: str = 'A:Z') -> List[Dict]:
        """Fetch data from Google Sheets"""
        try:
            service = self._get_service(access_token)
            
            # Get values
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # Convert to list of dictionaries using first row as headers
            headers = values[0] if values else []
            data_rows = values[1:] if len(values) > 1 else []
            
            formatted_data = []
            for row in data_rows:
                # Pad row with empty strings if shorter than headers
                padded_row = row + [''] * (len(headers) - len(row))
                row_dict = dict(zip(headers, padded_row))
                formatted_data.append(row_dict)
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch sheet data: {str(e)}")
            raise

    def update_sheet(self, sheet_id: str, data: List[Dict], access_token: str):
        """Update Google Sheets with data"""
        try:
            if not data:
                return
            
            service = self._get_service(access_token)
            
            # Prepare data for batch update
            headers = list(data[0].keys()) if data else []
            values = [headers]  # Start with headers
            
            for row in data:
                row_values = [str(row.get(header, '')) for header in headers]
                values.append(row_values)
            
            # Clear existing content first
            service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range='A:Z',
                body={}
            ).execute()
            
            # Update with new data
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='A1',
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            
            self.logger.info(f"Updated sheet with {len(data)} rows")
            
        except Exception as e:
            self.logger.error(f"Failed to update sheet: {str(e)}")
            raise

    def append_to_sheet(self, sheet_id: str, data: List[Dict], access_token: str):
        """Append data to Google Sheets"""
        try:
            if not data:
                return
                
            service = self._get_service(access_token)
            
            headers = list(data[0].keys()) if data else []
            values = []
            
            for row in data:
                row_values = [str(row.get(header, '')) for header in headers]
                values.append(row_values)
            
            service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range='A1',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': values}
            ).execute()
            
        except Exception as e:
            self.logger.error(f"Failed to append to sheet: {str(e)}")
            raise

    def get_sheet_info(self, sheet_id: str, access_token: str) -> Dict:
        """Get sheet metadata"""
        try:
            service = self._get_service(access_token)
            
            result = service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()
            
            return {
                'title': result.get('properties', {}).get('title', ''),
                'sheets': [
                    {
                        'title': sheet.get('properties', {}).get('title', ''),
                        'id': sheet.get('properties', {}).get('sheetId', 0)
                    }
                    for sheet in result.get('sheets', [])
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get sheet info: {str(e)}")
            raise

    def _get_service(self, access_token: str):
        """Create Google Sheets API service"""
        credentials = Credentials(token=access_token)
        service = build('sheets', 'v4', credentials=credentials)
        return service