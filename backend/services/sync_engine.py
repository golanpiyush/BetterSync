# services/sync_engine.py
import logging
from datetime import datetime
from models.log import SyncLog
from models.sync import Sync
from app import db

class SyncEngine:
    def __init__(self, notion_service, sheets_service):
        self.notion_service = notion_service
        self.sheets_service = sheets_service
        self.logger = logging.getLogger(__name__)

    def run_sync(self, sync):
        """Main sync execution method"""
        try:
            self._log_sync_start(sync)
            
            if sync.sync_direction in ['notion_to_sheets', 'both']:
                self._sync_notion_to_sheets(sync)
            
            if sync.sync_direction in ['sheets_to_notion', 'both']:
                self._sync_sheets_to_notion(sync)
            
            # Update last sync time
            sync.last_sync = datetime.utcnow()
            sync.status = 'active'
            db.session.commit()
            
            self._log_sync_success(sync)
            return {'status': 'success', 'message': 'Sync completed successfully'}
            
        except Exception as e:
            self.logger.error(f"Sync {sync.id} failed: {str(e)}")
            self._log_sync_error(sync, str(e))
            sync.status = 'error'
            db.session.commit()
            raise

    def _sync_notion_to_sheets(self, sync):
        """Sync from Notion to Google Sheets"""
        # Get user tokens
        user = sync.user
        
        # Fetch Notion data
        notion_data = self.notion_service.get_database_rows(
            sync.notion_database_id,
            user.notion_access_token,
            filters=sync.filters
        )
        
        # Transform data according to mapping
        transformed_data = self._transform_notion_to_sheets(notion_data, sync.mapping)
        
        # Update Google Sheets
        self.sheets_service.update_sheet(
            sync.sheet_id,
            transformed_data,
            user.google_access_token
        )
        
        self.logger.info(f"Synced {len(transformed_data)} rows from Notion to Sheets")

    def _sync_sheets_to_notion(self, sync):
        """Sync from Google Sheets to Notion"""
        # Get user tokens
        user = sync.user
        
        # Fetch Sheets data
        sheets_data = self.sheets_service.get_sheet_data(
            sync.sheet_id,
            user.google_access_token
        )
        
        # Apply filters if any
        filtered_data = self._apply_filters(sheets_data, sync.filters)
        
        # Transform data according to mapping
        transformed_data = self._transform_sheets_to_notion(filtered_data, sync.mapping)
        
        # Update Notion database
        self.notion_service.update_database_rows(
            sync.notion_database_id,
            transformed_data,
            user.notion_access_token
        )
        
        self.logger.info(f"Synced {len(transformed_data)} rows from Sheets to Notion")

    def _transform_notion_to_sheets(self, notion_data, mapping):
        """Transform Notion data format to Sheets format"""
        transformed = []
        
        for row in notion_data:
            sheets_row = {}
            
            for notion_field, sheets_col in mapping.items():
                value = row.get('properties', {}).get(notion_field, {})
                
                # Handle different Notion property types
                if value.get('type') == 'title':
                    sheets_row[sheets_col] = self._extract_title_text(value)
                elif value.get('type') == 'rich_text':
                    sheets_row[sheets_col] = self._extract_rich_text(value)
                elif value.get('type') == 'number':
                    sheets_row[sheets_col] = value.get('number', '')
                elif value.get('type') == 'select':
                    sheets_row[sheets_col] = value.get('select', {}).get('name', '')
                elif value.get('type') == 'relation':
                    # KEY FEATURE: Show relation names instead of IDs
                    sheets_row[sheets_col] = self._resolve_relation_names(value, notion_field)
                elif value.get('type') == 'date':
                    date_obj = value.get('date', {})
                    sheets_row[sheets_col] = date_obj.get('start', '') if date_obj else ''
                else:
                    sheets_row[sheets_col] = str(value.get('plain_text', ''))
            
            transformed.append(sheets_row)
        
        return transformed

    def _resolve_relation_names(self, relation_value, field_name):
        """Resolve relation IDs to readable names - KEY DIFFERENTIATOR"""
        try:
            relation_ids = [rel.get('id') for rel in relation_value.get('relation', [])]
            names = []
            
            for relation_id in relation_ids:
                # Fetch the related page to get its title
                related_page = self.notion_service.get_page(relation_id)
                if related_page:
                    title = self._extract_page_title(related_page)
                    names.append(title)
            
            return ', '.join(names) if names else ''
            
        except Exception as e:
            self.logger.warning(f"Failed to resolve relation names: {str(e)}")
            return ''

    def _extract_title_text(self, title_property):
        """Extract plain text from Notion title property"""
        try:
            title_array = title_property.get('title', [])
            return ''.join([t.get('plain_text', '') for t in title_array])
        except:
            return ''

    def _extract_rich_text(self, rich_text_property):
        """Extract plain text from Notion rich text property"""
        try:
            rich_text_array = rich_text_property.get('rich_text', [])
            return ''.join([rt.get('plain_text', '') for rt in rich_text_array])
        except:
            return ''

    def _apply_filters(self, data, filters):
        """Apply conditional filters to data"""
        if not filters:
            return data
        
        filtered_data = []
        for row in data:
            include_row = True
            
            for field, condition in filters.items():
                field_value = str(row.get(field, '')).lower()
                filter_value = str(condition.get('value', '')).lower()
                operator = condition.get('operator', 'equals')
                
                if operator == 'equals' and field_value != filter_value:
                    include_row = False
                    break
                elif operator == 'contains' and filter_value not in field_value:
                    include_row = False
                    break
                elif operator == 'not_empty' and not field_value:
                    include_row = False
                    break
            
            if include_row:
                filtered_data.append(row)
        
        return filtered_data

    def _log_sync_start(self, sync):
        log = SyncLog(
            sync_id=sync.id,
            status='started',
            message='Sync started',
            created_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

    def _log_sync_success(self, sync):
        log = SyncLog(
            sync_id=sync.id,
            status='completed',
            message='Sync completed successfully',
            created_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

    def _log_sync_error(self, sync, error_message):
        log = SyncLog(
            sync_id=sync.id,
            status='error',
            message=f'Sync failed: {error_message}',
            created_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()