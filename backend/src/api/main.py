# src/api/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from bson.objectid import ObjectId

from src.utils.database_handler import MedicalResearchDB
from src.assistant.medical_research_assistant import MedicalResearchAssistant

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('medical_research.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Medical Research Assistant API",
    description="API for medical research trends and queries",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Query(BaseModel):
    text: str

class AnalysisSummary(BaseModel):
    date: str
    type: str
    summary: str
    timestamp: str

class DailySummaries(BaseModel):
    date: str
    recent_trends: Optional[str] = None
    clinical: Optional[str] = None
    research: Optional[str] = None

    class Config:
        extra = "allow"  # Allows additional fields in the response

class QueryResponse(BaseModel):
    query: str
    response: str
    timestamp: str

# Initialize components
db = MedicalResearchDB()
assistant = MedicalResearchAssistant()
scheduler = BackgroundScheduler()

async def update_daily_analyses():
    """Background task to update analyses"""
    current_time = datetime.now()
    logger.info(f"Starting scheduled update at {current_time}")

    try:
        # Define analysis types
        analyses_to_update = [
            ("recent_trends", "recent_trends"),
            ("clinical", "clinical"),
            ("research", "research")
        ]

        # Connect to DB once
        db.connect()

        # Store today's date
        today = current_time.strftime("%Y-%m-%d")

        for analysis_type, query_type in analyses_to_update:
            try:
                logger.info(f"Updating {analysis_type} for date {today}")
                analysis = assistant.fetch_analysis(query_type)

                if analysis:
                    # Store with today's date
                    success = db.store_daily_analysis(
                        analysis_type,
                        analysis,
                        {
                            "updated_at": current_time.isoformat(),
                            "date": today,
                            "analysis_type": analysis_type
                        }
                    )

                    if success:
                        logger.info(f"Successfully updated {analysis_type} for {today}")
                    else:
                        logger.error(f"Failed to store {analysis_type} analysis for {today}")
                else:
                    logger.error(f"No analysis content generated for {analysis_type}")

            except Exception as e:
                logger.error(f"Error updating {analysis_type}: {str(e)}")

        logger.info(f"Daily update completed for {today}")

    except Exception as e:
        logger.error(f"Error in daily update: {str(e)}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler and run initial check on startup"""
    try:
        # Schedule daily update at midnight
        scheduler.add_job(
            update_daily_analyses,
            CronTrigger(hour=0, minute=0),
            id='daily_update',
            name='Daily Medical Research Update',
            replace_existing=True
        )

        scheduler.start()
        logger.info("Scheduler started successfully")

        try:
            # Run initial check
            status = await check_initial_update()
            logger.info(f"Initial check complete: {status}")
        except Exception as check_error:
            logger.error(f"Error during initial check: {check_error}")
            # Continue even if initial check fails
            # The scheduler is still running for future updates

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler gracefully"""
    scheduler.shutdown()
    logger.info("Scheduler shut down")

@app.get("/analyses/dates", response_model=List[str])
async def get_analysis_dates():
    """Get list of available dates with analyses"""
    try:
        db.connect()
        collection = db.db["daily_analysis"]
        dates = collection.distinct("date")
        dates.sort(reverse=True)
        return dates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/analyses/latest", response_model=DailySummaries)
async def get_latest_analyses():
    """Get the most recent analyses"""
    try:
        db.connect()
        collection = db.db["daily_analysis"]

        # Debug print
        print("Fetching latest analyses...")

        # Get the most recent date first
        latest_date = collection.find_one(
            sort=[("date", -1)]
        )["date"]

        print(f"Latest date found: {latest_date}")

        # Now get all analyses for this date
        result = DailySummaries(date=latest_date)

        # Fetch all documents for the latest date
        latest_analyses = collection.find({"date": latest_date})

        # Populate the result object
        for analysis in latest_analyses:
            print(f"Processing analysis type: {analysis['type']}")
            if analysis["type"] == "recent_trends":
                result.recent_trends = analysis["summary"]
            elif analysis["type"] == "clinical":
                result.clinical = analysis["summary"]
            elif analysis["type"] == "research":
                result.research = analysis["summary"]

        return result

    except Exception as e:
        print(f"Error in get_latest_analyses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving latest analyses: {str(e)}"
        )
    finally:
        db.close()


@app.get("/analyses/stats/summary")
async def get_analysis_stats():
    """Get summary statistics about available analyses"""
    try:
        db.connect()
        collection = db.db["daily_analysis"]

        total_docs = collection.count_documents({})
        unique_dates = len(collection.distinct("date"))
        analysis_types = collection.distinct("type")

        type_counts = {}
        for analysis_type in analysis_types:
            type_counts[analysis_type] = collection.count_documents({"type": analysis_type})

        latest_doc = collection.find_one(sort=[("date", -1)])
        latest_date = latest_doc["date"] if latest_doc else None

        return {
            "total_analyses": total_docs,
            "unique_dates": unique_dates,
            "analysis_types": analysis_types,
            "type_counts": type_counts,
            "latest_date": latest_date,
            "status": "active" if latest_date else "no data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/analyses/{date}", response_model=DailySummaries)
async def get_analyses_by_date(date: str):
    """Get all analyses for a specific date"""
    try:
        db.connect()
        collection = db.db["daily_analysis"]

        # Find all analyses for the given date
        analyses = collection.find({"date": date})

        result = DailySummaries(date=date)
        has_data = False

        for analysis in analyses:
            has_data = True
            if analysis["type"] == "recent_trends":
                result.recent_trends = analysis["summary"]
            elif analysis["type"] == "clinical":
                result.clinical = analysis["summary"]
            elif analysis["type"] == "research":
                result.research = analysis["summary"]

        if not has_data:
            raise HTTPException(status_code=404, detail=f"No analyses found for date: {date}")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/query", response_model=QueryResponse)
async def process_query(query: Query):
    """Process a user query"""
    try:
        response = assistant.answer_specific_query(query.text)

        return QueryResponse(
            query=query.text,
            response=response,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-analyses")
async def trigger_update(background_tasks: BackgroundTasks):
    """Manually trigger analyses update"""
    try:
        logger.info("Manually triggering analyses update...")

        # Instead of individual tasks, add the main update function
        background_tasks.add_task(update_daily_analyses)

        current_time = datetime.now()
        return {
            "message": "Update initiated",
            "success": True,
            "timestamp": current_time.isoformat(),
            "details": "Updates for all analysis types have been queued"
        }

    except Exception as e:
        logger.error(f"Error triggering update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database content"""
    try:
        db.connect()
        collection = db.db["daily_analysis"]

        # Get all documents, sorted by date
        all_docs = list(collection.find().sort("date", -1))

        # Convert ObjectId to string for JSON serialization
        for doc in all_docs:
            doc["_id"] = str(doc["_id"])

        return {
            "total_documents": len(all_docs),
            "sample_documents": all_docs[:5],  # Show first 5 documents
            "unique_dates": collection.distinct("date"),
            "unique_types": collection.distinct("type"),
            "collection_name": collection.name,
            "database_name": db.db.name
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error accessing database: {str(e)}"
        )
    finally:
        db.close()

@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get the status of the background scheduler"""
    try:
        jobs = scheduler.get_jobs()
        return {
            "status": "running" if scheduler.running else "stopped",
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "pending": job.pending
                }
                for job in jobs
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting scheduler status: {str(e)}"
        )

@app.get("/scheduler/initial-check")
async def check_initial_update():
    """Check initial update status and calculate next update time"""
    try:
        today = datetime.now().date()
        midnight = datetime.min.time()
        next_run = datetime.combine(today + timedelta(days=1), midnight)
        current_time = datetime.now()
        time_until_next = next_run - current_time

        total_seconds = time_until_next.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        try:
            db.connect()
            collection = db.db["daily_analysis"]

            # Check for today's data specifically
            todays_data = collection.find_one({"date": today.strftime("%Y-%m-%d")})

            needs_update = True if not todays_data else False

            if needs_update:
                logger.info(f"No data found for today ({today}), triggering update...")
                # Run update directly instead of using background tasks
                await update_daily_analyses()
                message = "Initial update completed. "
            else:
                logger.info("Today's data is already present")
                message = "Data is up to date. "

            next_update_time = next_run.strftime('%Y-%m-%d %H:%M:%S')
            message += f"Next update scheduled for {next_update_time}"
            logger.info(message)

            return {
                "message": message,
                "next_update": next_run.isoformat(),
                "hours_until_next": hours,
                "minutes_until_next": minutes,
                "needs_update": needs_update,
                "current_time": current_time.isoformat(),
                "next_update_time": next_update_time
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in initial check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking initial update: {str(e)}"
        )
