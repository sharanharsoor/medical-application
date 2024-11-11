import certifi
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

class MedicalResearchDB:
    def __init__(self):
        """Initialize MongoDB connection for medical research data"""
        self.username = "sharan"
        self.password = "sharan123"
        self.cluster_url = "cluster0.t7u2a.mongodb.net"
        self.database_name = "medical_data"
        self.uri = f"mongodb+srv://{self.username}:{self.password}@{self.cluster_url}/?retryWrites=true&w=majority"
        self.client = None
        self.db = None

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.uri, tlsCAFile=certifi.where())
            self.db = self.client[self.database_name]
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

    def store_daily_analysis(self,
                           analysis_type: str,
                           summary_text: str,
                           metadata: Optional[Dict] = None) -> bool:
        """
        Store daily analysis results

        Args:
            analysis_type: "trends", "clinical", or "research"
            summary_text: The analysis text to store
            metadata: Additional metadata about the analysis
        """
        try:
            collection = self.db["daily_analysis"]

            today = datetime.now().strftime('%Y-%m-%d')

            document = {
                "date": today,
                "type": analysis_type,
                "summary": summary_text,
                "timestamp": datetime.now(),
                "metadata": metadata or {}
            }

            # Update if exists for today, insert if not
            result = collection.update_one(
                {"date": today, "type": analysis_type},
                {"$set": document},
                upsert=True
            )

            print(f"Stored {analysis_type} analysis for {today}")
            return True

        except Exception as e:
            print(f"Error storing {analysis_type} analysis: {e}")
            return False

    def get_latest_analysis(self, analysis_type: str) -> Optional[str]:
        """Get most recent analysis of specified type"""
        try:
            collection = self.db["daily_analysis"]
            document = collection.find_one(
                {"type": analysis_type},
                sort=[("timestamp", -1)]
            )

            if document:
                return document["summary"]
            print(f"No {analysis_type} analysis found")
            return None

        except Exception as e:
            print(f"Error retrieving {analysis_type} analysis: {e}")
            return None

    def store_query_result(self,
                          query: str,
                          response: str,
                          metadata: Optional[Dict] = None) -> bool:
        """Store user query and its response"""
        try:
            collection = self.db["query_history"]

            document = {
                "timestamp": datetime.now(),
                "query": query,
                "response": response,
                "metadata": metadata or {}
            }

            collection.insert_one(document)
            return True

        except Exception as e:
            print(f"Error storing query result: {e}")
            return False

    def get_recent_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent user queries and responses"""
        try:
            collection = self.db["query_history"]
            cursor = collection.find().sort("timestamp", -1).limit(limit)
            return list(cursor)

        except Exception as e:
            print(f"Error retrieving recent queries: {e}")
            return []