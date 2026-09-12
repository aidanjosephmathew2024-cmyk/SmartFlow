from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import traffic_logs

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "SmartFlow backend is running"}


@app.get("/traffic")
def get_traffic():
    # Fetch real documents from MongoDB, most recent first
    results = traffic_logs.find().sort("timestamp", -1).limit(20)

    # Convert MongoDB documents to JSON-friendly format
    traffic_data = []
    for doc in results:
        doc["_id"] = str(doc["_id"])  # ObjectId isn't JSON-serializable by default
        traffic_data.append(doc)

    return traffic_data