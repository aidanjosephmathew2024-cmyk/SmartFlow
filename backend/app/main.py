from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import traffic_logs, db

app = FastAPI()

camera_status = db["camera_status"]

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
    results = traffic_logs.find().sort("timestamp", -1).limit(20)
    traffic_data = []
    for doc in results:
        doc["_id"] = str(doc["_id"])
        traffic_data.append(doc)
    return traffic_data


@app.get("/camera-status")
def get_camera_status():
    status = camera_status.find_one({"_id": "current"})
    if status:
        status["_id"] = str(status["_id"])
        return status
    return {"current_road": None, "status": "unknown", "last_updated": None}