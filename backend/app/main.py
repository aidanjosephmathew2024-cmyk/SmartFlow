from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import traffic_logs, db
from bson import ObjectId

app = FastAPI(title="SmartFlow API")

camera_status = db["camera_status"]
@app.delete("/traffic/{document_id}")
def delete_traffic_document(document_id: str):
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=400, detail="Invalid document ID")

    result = traffic_logs.delete_one({"_id": ObjectId(document_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Traffic record not found")

    return {"deleted": True}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parsed_timestamp_stage():
    """
    Convert the timestamp string in each MongoDB document into a date.
    Invalid or missing timestamps become None.
    """
    return {
        "$addFields": {
            "_parsed_timestamp": {
                "$convert": {
                    "input": "$timestamp",
                    "to": "date",
                    "onError": None,
                    "onNull": None,
                }
            }
        }
    }


def as_iso_string(value):
    """Return a JSON-friendly ISO string for a MongoDB date."""
    return value.isoformat() if value else None


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

    return {
        "current_road": None,
        "status": "unknown",
        "last_updated": None,
    }


@app.get("/stats/summary")
def get_stats_summary():
    summary_pipeline = [
        parsed_timestamp_stage(),
        {"$match": {"_parsed_timestamp": {"$ne": None}}},
        {
            "$group": {
                "_id": None,
                "records_analyzed": {"$sum": 1},
                "cars": {"$sum": {"$ifNull": ["$cars", 0]}},
                "bikes": {"$sum": {"$ifNull": ["$bikes", 0]}},
                "buses": {"$sum": {"$ifNull": ["$bus", 0]}},
                "trucks": {"$sum": {"$ifNull": ["$truck", 0]}},
                "ambulance_records": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$ambulance", True]},
                            1,
                            0,
                        ]
                    }
                },
                "average_green_time": {"$avg": "$green_time"},
                "first_record": {"$min": "$_parsed_timestamp"},
                "latest_record": {"$max": "$_parsed_timestamp"},
            }
        },
    ]

    road_pipeline = [
        parsed_timestamp_stage(),
        {"$match": {"_parsed_timestamp": {"$ne": None}}},
        {
            "$group": {
                "_id": "$road",
                "records": {"$sum": 1},
                "cars": {"$sum": {"$ifNull": ["$cars", 0]}},
                "bikes": {"$sum": {"$ifNull": ["$bikes", 0]}},
                "buses": {"$sum": {"$ifNull": ["$bus", 0]}},
                "trucks": {"$sum": {"$ifNull": ["$truck", 0]}},
                "average_green_time": {"$avg": "$green_time"},
                "average_priority_score": {"$avg": "$priority_score"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    congestion_pipeline = [
        parsed_timestamp_stage(),
        {"$match": {"_parsed_timestamp": {"$ne": None}}},
        {
            "$group": {
                "_id": "$congestion",
                "records": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    summary_results = list(traffic_logs.aggregate(summary_pipeline))
    road_results = list(traffic_logs.aggregate(road_pipeline))
    congestion_results = list(traffic_logs.aggregate(congestion_pipeline))

    summary = summary_results[0] if summary_results else {}

    return {
        "records_analyzed": summary.get("records_analyzed", 0),
        "date_range": {
            "from": as_iso_string(summary.get("first_record")),
            "to": as_iso_string(summary.get("latest_record")),
        },
        "vehicle_totals": {
            "cars": summary.get("cars", 0),
            "bikes": summary.get("bikes", 0),
            "buses": summary.get("buses", 0),
            "trucks": summary.get("trucks", 0),
        },
        "ambulance_records": summary.get("ambulance_records", 0),
        "average_green_time": summary.get("average_green_time"),
        "by_road": [
            {
                "road": result["_id"],
                "records": result["records"],
                "cars": result["cars"],
                "bikes": result["bikes"],
                "buses": result["buses"],
                "trucks": result["trucks"],
                "average_green_time": result["average_green_time"],
                "average_priority_score": result["average_priority_score"],
            }
            for result in road_results
        ],
        "congestion": [
            {
                "level": result["_id"],
                "records": result["records"],
            }
            for result in congestion_results
        ],
    }


@app.get("/stats/trends")
def get_stats_trends(days: int = 30):
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 365",
        )

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    trend_pipeline = [
        parsed_timestamp_stage(),
        {
            "$match": {
                "_parsed_timestamp": {
                    "$ne": None,
                    "$gte": start_date,
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$_parsed_timestamp",
                        "timezone": "UTC",
                    }
                },
                "records": {"$sum": 1},
                "cars": {"$sum": {"$ifNull": ["$cars", 0]}},
                "bikes": {"$sum": {"$ifNull": ["$bikes", 0]}},
                "buses": {"$sum": {"$ifNull": ["$bus", 0]}},
                "trucks": {"$sum": {"$ifNull": ["$truck", 0]}},
                "ambulance_records": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$ambulance", True]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]

    results = list(traffic_logs.aggregate(trend_pipeline))

    return {
        "days": days,
        "data": [
            {
                "date": result["_id"],
                "records": result["records"],
                "cars": result["cars"],
                "bikes": result["bikes"],
                "buses": result["buses"],
                "trucks": result["trucks"],
                "ambulance_records": result["ambulance_records"],
            }
            for result in results
        ],
    }