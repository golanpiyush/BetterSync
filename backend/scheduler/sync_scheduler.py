# scheduler/sync_scheduler.py
import schedule
import time
import threading
from datetime import datetime, timedelta
from models.sync import Sync
from services.sync_engine import SyncEngine
from services.notion_service import NotionService
from services.sheets_service import SheetsService
import logging

class SyncScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sync_engine = SyncEngine(NotionService(), SheetsService())
        self.running = False

    def start(self):
        """Start the scheduler in a separate thread"""
        self.running = True
        self.logger.info("Starting sync scheduler...")
        
        # Schedule different frequencies
        schedule.every(5).minutes.do(self._run_realtime_syncs)
        schedule.every(1).hours.do(self._run_hourly_syncs)
        schedule.every().day.at("02:00").do(self._run_daily_syncs)
        schedule.every().week.do(self._run_weekly_syncs)
        
        # Run scheduler in background thread
        scheduler_thread = threading.Thread(target=self._scheduler_worker)
        scheduler_thread.daemon = True
        scheduler_thread.start()

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        self.logger.info("Sync scheduler stopped")

    def _scheduler_worker(self):
        """Background worker that runs scheduled tasks"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying

    def _run_realtime_syncs(self):
        """Run syncs that are set to real-time frequency"""
        self._run_syncs_by_frequency('realtime')

    def _run_hourly_syncs(self):
        """Run syncs that are set to hourly frequency"""
        self._run_syncs_by_frequency('hourly')

    def _run_daily_syncs(self):
        """Run syncs that are set to daily frequency"""
        self._run_syncs_by_frequency('daily')

    def _run_weekly_syncs(self):
        """Run syncs that are set to weekly frequency"""
        self._run_syncs_by_frequency('weekly')

    def _run_syncs_by_frequency(self, frequency: str):
        """Run all active syncs with the specified frequency"""
        try:
            syncs = Sync.query.filter_by(
                frequency=frequency,
                status='active'
            ).all()
            
            for sync in syncs:
                # Check if enough time has passed since last sync
                if self._should_run_sync(sync, frequency):
                    try:
                        self.logger.info(f"Running scheduled sync: {sync.name}")
                        self.sync_engine.run_sync(sync)
                    except Exception as e:
                        self.logger.error(f"Failed to run sync {sync.id}: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Error running {frequency} syncs: {str(e)}")

    def _should_run_sync(self, sync, frequency: str) -> bool:
        """Check if enough time has passed to run the sync again"""
        if not sync.last_sync:
            return True
            
        now = datetime.utcnow()
        time_since_last = now - sync.last_sync
        
        frequency_intervals = {
            'realtime': timedelta(minutes=5),
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1)
        }
        
        required_interval = frequency_intervals.get(frequency, timedelta(hours=1))
        return time_since_last >= required_interval

# Initialize and start scheduler
scheduler = SyncScheduler()

def start_scheduler():
    scheduler.start()

def stop_scheduler():
    scheduler.stop()