import schedule
import time
from datetime import datetime
from typing import Optional

from ..assistant.medical_research_assistant import MedicalResearchAssistant
from .database_handler import MedicalResearchDB

class DailyAnalysisUpdater:
    def __init__(self, assistant: Optional[MedicalResearchAssistant] = None):
        """Initialize updater with optional assistant instance"""
        self.assistant = assistant or MedicalResearchAssistant()
        self.db = MedicalResearchDB()

    def update_all_analyses(self):
        """Update all types of analyses"""
        try:
            self.db.connect()

            # Update trends analysis
            trends = self.assistant.fetch_analysis("recent_trends")
            self.db.store_daily_analysis(
                "trends",
                trends,
                {"source": "multiple", "analysis_type": "trends"}
            )

            # Update clinical analysis
            clinical = self.assistant.fetch_analysis("clinical")
            self.db.store_daily_analysis(
                "clinical",
                clinical,
                {"source": "multiple", "analysis_type": "clinical"}
            )

            # Update research analysis
            research = self.assistant.fetch_analysis("research")
            self.db.store_daily_analysis(
                "research",
                research,
                {"source": "multiple", "analysis_type": "research"}
            )

            print(f"Successfully updated all analyses at {datetime.now()}")

        except Exception as e:
            print(f"Error updating analyses: {e}")
        finally:
            self.db.close()

    def start_scheduler(self, update_time: str = "00:00"):
        """Start the daily update scheduler"""
        print(f"Starting scheduler, will update daily at {update_time}")

        schedule.every().day.at(update_time).do(self.update_all_analyses)

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def update_now(self):
        """Manually trigger an update"""
        print("Manually triggering analysis update...")
        self.update_all_analyses()