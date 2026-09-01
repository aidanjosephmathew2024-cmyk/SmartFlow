from ultralytics import YOLO
import cv2
import statistics
from datetime import datetime
from db import traffic_logs  # import the collection from db.py

model = YOLO("yolov8n.pt")
video_path = "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/test_traffic.mp4"

VEHICLE_CLASSES = {2: "car", 3: "bike", 5: "bus", 7: "truck"}

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

all_frame_counts = {"car": [], "bike": [], "bus": [], "truck": []}
frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    results = model(frame, verbose=False)

    counts = {"car": 0, "bike": 0, "bus": 0, "truck": 0}
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        if class_id in VEHICLE_CLASSES:
            counts[VEHICLE_CLASSES[class_id]] += 1

    for vtype in all_frame_counts:
        all_frame_counts[vtype].append(counts[vtype])

    annotated_frame = results[0].plot()
    cv2.imshow("SmartFlow - Vehicle Detection", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Aggregate final scan result
final_scan = {}
for vtype, values in all_frame_counts.items():
    final_scan[vtype] = statistics.mode(values) if values else 0

print("\n--- Final Scan Result (aggregated) ---")
print(final_scan)

# ---- Build the document matching your canonical JSON format ----
document = {
    "timestamp": datetime.now().isoformat(),
    "road": "North",  # hardcoded for now, will change per rotation later
    "cars": final_scan["car"],
    "bikes": final_scan["bike"],
    "bus": final_scan["bus"],
    "truck": final_scan["truck"],
    "ambulance": False,  # placeholder until Week 3 ambulance detection is built
    "congestion": "Medium",  # placeholder until congestion detection is built
    "priority_score": None,  # will be filled by SAPE later
    "green_time": None  # will be filled by SAPE later
}

# ---- Insert into MongoDB ----
result = traffic_logs.insert_one(document)
print(f"\n✅ Inserted into traffic_logs with ID: {result.inserted_id}")