import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture("road.mp4")

while True:

    success, frame = cap.read()

    if not success:
        break

    results = model(frame)

    annotated_frame = results[0].plot()

    car_count = 0
    person_count = 0

    for box in results[0].boxes:

        class_id = int(box.cls[0])

        class_name = model.names[class_id]

        if class_name == "car":
            car_count += 1

        elif class_name == "person":
            person_count += 1
    risk = "LOW"

    if car_count > 8:
        risk = "MEDIUM"

    if car_count > 15:
        risk = "HIGH"

    if person_count > 3:
        risk = "HIGH"

    cv2.putText(
        annotated_frame,
        f"Cars: {car_count}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )

    cv2.putText(
        annotated_frame,
        f"People: {person_count}",
        (20,80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )

    cv2.putText(
    annotated_frame,
    f"Risk: {risk}",
    (20,120),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    (0,0,255),
    2
)

    annotated_frame = cv2.resize(annotated_frame, (1280, 720))
    cv2.imshow("AI Driving Copilot", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()