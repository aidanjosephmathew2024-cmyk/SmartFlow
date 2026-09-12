from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
MONGODB_URI= os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client["smartflow_db"]

traffic_logs = db["traffic_logs"]