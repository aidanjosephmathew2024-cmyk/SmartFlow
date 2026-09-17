from ultralytics import YOLO

def main():
    model = YOLO('yolov8n.pt')

    results = model.train(
        data='datasets/roboflow-ambulance/data.yaml',
        epochs=50,
        imgsz=640,
        batch=8,
        device=0,
        workers=2,
        patience=15,
        project='models',
        name='ambulance_detector',
        exist_ok=True
    )

if __name__ == '__main__':
    main()