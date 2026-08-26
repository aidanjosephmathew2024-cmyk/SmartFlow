from ultralytics import YOLO
import cv2
from collections import Counter
import statistics

model = YOLO("yolov8n.pt")
video_path = "C:/Users/ASUS/Desktop/SmartFlow/ai-module/datasets/roboflow-ambulance/sample_videos/test_traffic.mp4"

VEHICLE_CLASSES = {2: "car", 3: "bike", 5: "bus", 7: "truck"}

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Store per-frame counts across the whole video
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

# ---- AGGREGATION: simulate one "scan" result from all frames ----
final_scan = {}
for vtype, values in all_frame_counts.items():
    # mode = most frequently occurring count across frames (smooths out flicker)
    final_scan[vtype] = statistics.mode(values) if values else 0

print("\n--- Final Scan Result (aggregated) ---")
print(final_scan)