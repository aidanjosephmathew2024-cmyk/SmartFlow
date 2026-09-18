from ultralytics import YOLO
import cv2
import statistics
import time
from datetime import datetime
from db import traffic_logs, camera_logs, db
from sape import run_sape, calculate_congestion

general_model = YOLO("yolov8n.pt")
ambulance_model = YOLO("../runs/detect/models/vehicle_ambulance_detector/weights/best.pt")

GENERAL_CLASSES = {2: "car", 3: "bike", 5: "bus", 7: "truck"}
AMBULANCE_CLASS_ID = 4
AMBULANCE_CONF_THRESHOLD = 0.5

ROAD_VIDEOS = {
    "North": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/north.mp4",
    "East": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/east.mp4",
    "South": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/south.mp4",
    "West": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/west.mp4",
}

FRAMES_PER_SCAN = 10
ROTATION_INTERVAL_SEC = 3

camera_status = db["camera_status"]

latest_road_data = {
    road: {"cars": 0, "bikes": 0, "bus": 0, "truck": 0, "ambulance": False, "congestion": "Medium"}
    for road in ROAD_VIDEOS
}

road_frame_positions = {road: 0 for road in ROAD_VIDEOS}


def scan_road(road_name, video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"⚠️ Could not open video for {road_name}")
        return {"car": 0, "bike": 0, "bus": 0, "truck": 0, "ambulance": 0}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    start_pos = road_frame_positions[road_name]

    if start_pos >= total_frames - FRAMES_PER_SCAN:
        start_pos = 0

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_pos)

    frame_counts = {"car": [], "bike": [], "bus": [], "truck": [], "ambulance": []}
    frames_read = 0

    while frames_read < FRAMES_PER_SCAN:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frames_read += 1
        counts = {"car": 0, "bike": 0, "bus": 0, "truck": 0, "ambulance": 0}

        general_results = general_model(frame, verbose=False)
        for box in general_results[0].boxes:
            class_id = int(box.cls[0])
            if class_id in GENERAL_CLASSES:
                counts[GENERAL_CLASSES[class_id]] += 1

        amb_results = ambulance_model(frame, verbose=False)
        for box in amb_results[0].boxes:
            if int(box.cls[0]) == AMBULANCE_CLASS_ID and float(box.conf[0]) >= AMBULANCE_CONF_THRESHOLD:
                counts["ambulance"] += 1

        for vtype in frame_counts:
            frame_counts[vtype].append(counts[vtype])

    road_frame_positions[road_name] = start_pos + FRAMES_PER_SCAN
    cap.release()

    final_scan = {}
    for vtype, values in frame_counts.items():
        final_scan[vtype] = statistics.mode(values) if values else 0

    return final_scan


def run_rotation_cycle():
    for road_name, video_path in ROAD_VIDEOS.items():
        print(f"\n📷 Rotating to {road_name}... capturing {FRAMES_PER_SCAN} frames")

        camera_status.update_one(
            {"_id": "current"},
            {"$set": {
                "current_road": road_name,
                "status": "scanning",
                "last_updated": datetime.now().isoformat()
            }},
            upsert=True
        )

        scan_start = datetime.now()
        scan = scan_road(road_name, video_path)
        scan_end = datetime.now()

        latest_road_data[road_name]["cars"] = scan["car"]
        latest_road_data[road_name]["bikes"] = scan["bike"]
        latest_road_data[road_name]["bus"] = scan["bus"]
        latest_road_data[road_name]["truck"] = scan["truck"]
        latest_road_data[road_name]["ambulance"] = scan["ambulance"] > 0

        congestion_level = calculate_congestion({
            "cars": scan["car"],
            "bikes": scan["bike"],
            "bus": scan["bus"],
            "truck": scan["truck"]
        })
        latest_road_data[road_name]["congestion"] = congestion_level

        camera_logs.insert_one({
            "timestamp": scan_start.isoformat(),
            "road_captured": road_name,
            "frames_captured": FRAMES_PER_SCAN,
            "capture_duration_sec": (scan_end - scan_start).total_seconds(),
            "status": "success"
        })

        print(f"{road_name} result: {scan}")
        time.sleep(ROTATION_INTERVAL_SEC)

    sape_result = run_sape(latest_road_data)

    print("\n--- SAPE Result (Full Rotation Cycle) ---")
    print(f"TPS: {sape_result['tps']}")
    print(f"Green Times: {sape_result['green_times']}")

    for road, data in latest_road_data.items():
        document = {
            "timestamp": datetime.now().isoformat(),
            "road": road,
            "cars": data["cars"],
            "bikes": data["bikes"],
            "bus": data["bus"],
            "truck": data["truck"],
            "ambulance": data["ambulance"],
            "congestion": data["congestion"],
            "priority_score": sape_result["tps"][road] if sape_result["tps"] else None,
            "green_time": sape_result["green_times"][road]
        }
        traffic_logs.insert_one(document)

    print("\n✅ Rotation cycle complete. All 4 roads updated in traffic_logs.\n")


if __name__ == "__main__":
    print("🔄 Starting SmartFlow rotating camera simulation. Press Ctrl+C to stop.\n")
    try:
        while True:
            run_rotation_cycle()
    except KeyboardInterrupt:
        print("\n🛑 Rotation stopped by user.")