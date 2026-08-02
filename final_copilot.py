import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture("road.mp4")

while True:

    success, frame = cap.read()

    if not success:
        break

    results = model(frame, conf=0.8)

    annotated_frame = results[0].plot()

    car_count = 0
    person_count = 0

    collision_warning = False

    for box in results[0].boxes:

        class_id = int(box.cls[0])
        class_name = model.names[class_id]

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Count objects
        if class_name == "car":
            car_count += 1

            # Distance estimation using box area
            box_area = (x2 - x1) * (y2 - y1)

            frame_height, frame_width = frame.shape[:2]

            center_x = (x1 + x2) // 2

            if (
                box_area > 30000
                and center_x > frame_width * 0.35
                and center_x < frame_width * 0.65
                ):
                    collision_warning = True

        elif class_name == "person":
            person_count += 1

    # Risk Calculation
    risk = "LOW"

    if car_count > 8:
        risk = "MEDIUM"

    if car_count > 15:
        risk = "HIGH"

    if person_count > 3:
        risk = "HIGH"

    # Traffic Calculation
    if car_count < 5:
        traffic = "LOW"
    elif car_count < 10:
        traffic = "MEDIUM"
    else:
        traffic = "HIGH"

    # Display Information

    cv2.putText(
        annotated_frame,
        f"Cars: {car_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        annotated_frame,
        f"People: {person_count}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Risk: {risk}",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Traffic: {traffic}",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        2
    )

    # Collision Warning
    if collision_warning:
        cv2.putText(
            annotated_frame,
            "WARNING: VEHICLE TOO CLOSE!",
            (300, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

    annotated_frame = cv2.resize(
        annotated_frame,
        (1280, 720)
    )

    cv2.imshow(
        "AI Driving Copilot",
        annotated_frame
    )

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()