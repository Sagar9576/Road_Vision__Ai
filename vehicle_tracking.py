import cv2
import numpy as np
import time
from ultralytics import YOLO
import supervision as sv

# =====================
# LOAD MODEL
# =====================

model = YOLO("yolov8n.pt")

# =====================
# BYTE TRACK
# =====================

tracker = sv.ByteTrack()

# =====================
# VIDEO
# =====================

cap = cv2.VideoCapture("road.mp4")

prev_time = 0

# Store previous positions for speed estimation
previous_positions = {}

# COCO Vehicle Classes

vehicle_classes = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

while True:

    success, frame = cap.read()

    if not success:
        break

    # =====================
    # FPS
    # =====================

    current_time = time.time()

    fps = 1 / (current_time - prev_time + 0.0001)

    prev_time = current_time

    # =====================
    # YOLO DETECTION
    # =====================

    result = model(frame, verbose=False)[0]

    detections = sv.Detections.from_ultralytics(result)

    # =====================
    # VEHICLE FILTER
    # =====================

    mask = np.isin(
        detections.class_id,
        list(vehicle_classes.keys())
    )

    detections = detections[mask]

    # =====================
    # TRACKING
    # =====================

    detections = tracker.update_with_detections(
        detections
    )

    tracked_count = 0

    # =====================
    # DRAW TRACKS
    # =====================

    for box, tracker_id, class_id in zip(
        detections.xyxy,
        detections.tracker_id,
        detections.class_id
    ):

        if tracker_id is None:
            continue

        tracked_count += 1

        x1, y1, x2, y2 = map(int, box)

        # Vehicle Label
        label = vehicle_classes.get(
            int(class_id),
            "Vehicle"
        )

        # =====================
        # DISTANCE ESTIMATION
        # =====================

        box_area = (x2 - x1) * (y2 - y1)

        distance = max(1,int(800000 / (box_area + 1))
)

        # =====================
        # RELATIVE SPEED
        # =====================

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        motion = "Stable"

        if tracker_id in previous_positions:

            prev_y = previous_positions[
                tracker_id
            ]

            difference = center_y - prev_y

            if difference > 5:
                motion = "Approaching"

            elif difference < -5:
                motion = "Moving Away"

        previous_positions[
            tracker_id
        ] = center_y

        # =====================
        # DRAW BOX
        # =====================

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # =====================
        # DRAW LABEL
        # =====================

        cv2.putText(
            frame,
            f"{label} ID:{tracker_id}",
            (x1, y1 - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"{motion}",
            (x1, y1 - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"{distance}m",
            (x1, y2 + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 0),
            2
        )

    # =====================
    # INFO PANEL
    # =====================

    cv2.putText(
        frame,
        f"Tracked Vehicles: {tracked_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"FPS: {int(fps)}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    # =====================
    # RESIZE
    # =====================

    frame = cv2.resize(
        frame,
        (1280, 720)
    )

    cv2.imshow(
        "Vehicle Tracking V2",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()