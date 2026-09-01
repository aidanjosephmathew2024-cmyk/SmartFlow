from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client["smartflow_db"]

# Collections
traffic_logs = db["traffic_logs"]
events = db["events"]
signal_recommendations = db["signal_recommendations"]
camera_logs = db["camera_logs"]

# Quick connection test
if __name__ == "__main__":
    try:
        client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas successfully!")
        print(f"Collections found: {db.list_collection_names()}")
    except Exception as e:
        print("❌ Connection failed:", e)