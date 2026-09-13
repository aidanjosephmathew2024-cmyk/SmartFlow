from ultralytics import YOLO
import cv2
import statistics
from datetime import datetime
from db import traffic_logs
from sape import run_sape

model = YOLO("yolov8n.pt")

VEHICLE_CLASSES = {2: "car", 3: "bike", 5: "bus", 7: "truck"}

ROAD_VIDEOS = {
    "North": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/north.mp4",
    "East": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/east.mp4",
    "South": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/south.mp4",
    "West": "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/west.mp4",
}


def detect_and_count(video_path):
    """Run YOLO on one video, return aggregated vehicle counts."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: could not open {video_path}")
        return {"car": 0, "bike": 0, "bus": 0, "truck": 0}

    all_frame_counts = {"car": [], "bike": [], "bus": [], "truck": []}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)
        counts = {"car": 0, "bike": 0, "bus": 0, "truck": 0}
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            if class_id in VEHICLE_CLASSES:
                counts[VEHICLE_CLASSES[class_id]] += 1

        for vtype in all_frame_counts:
            all_frame_counts[vtype].append(counts[vtype])

    cap.release()

    final_scan = {}
    for vtype, values in all_frame_counts.items():
        final_scan[vtype] = statistics.mode(values) if values else 0

    return final_scan


# ---- STEP 1: Detect vehicles on all 4 roads ----
all_roads_data = {}

for road, path in ROAD_VIDEOS.items():
    print(f"\nProcessing {road}...")
    scan = detect_and_count(path)
    print(f"{road} result: {scan}")

    all_roads_data[road] = {
        "cars": scan["car"],
        "bikes": scan["bike"],
        "bus": scan["bus"],
        "truck": scan["truck"],
        "ambulance": False,  # placeholder until ambulance detection is built
        "congestion": "Medium"  # placeholder until congestion detection is built
    }

# ---- STEP 2: Run SAPE ONCE across all 4 roads together ----
sape_result = run_sape(all_roads_data)

print("\n--- SAPE Result (Full 4-Road Cycle) ---")
print(f"Emergency Override: {sape_result['emergency_override']}")
print(f"TPS per road: {sape_result['tps']}")
print(f"Green Times: {sape_result['green_times']}")

# ---- STEP 3: Insert one document per road, each with its REAL proportional green_time ----
for road, data in all_roads_data.items():
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
    result = traffic_logs.insert_one(document)
    print(f"✅ Inserted {road} scan with ID: {result.inserted_id}")