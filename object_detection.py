from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # pretrained model

def detect_object(image_path):
    results = model(image_path)

    labels = []
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]
            labels.append(label)

    return labels