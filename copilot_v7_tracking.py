import cv2
import numpy as np
import time
from ultralytics import YOLO
import ollama
import supervision as sv
from sentence_transformers import SentenceTransformer
import faiss
import json

# =====================
# LOAD MODEL
# =====================

model = YOLO("yolov8n.pt")
tracker = sv.ByteTrack()
sign_model = YOLO(
r"C:\Users\skku8\Downloads\traffic_sign\runs\detect\train-3\weights\best.pt"
)
# RAG SETUP

with open("traffic_rules.txt", "r", encoding="utf-8") as f:
    rules = f.read().split("\n\n")

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

rule_embeddings = embed_model.encode(rules)

index = faiss.IndexFlatL2(rule_embeddings.shape[1])

index.add(np.array(rule_embeddings))

# =====================
# LOAD VIDEO
# =====================

cap = cv2.VideoCapture("road.mp4")

prev_time = 0
last_llm_time = 0
ai_advice = "Analyzing road..."
previous_positions = {}

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
    # LANE DETECTION
    # =====================

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    edges = cv2.Canny(
        blur,
        50,
        150
    )

    height, width = edges.shape

    mask = np.zeros_like(edges)

    polygon = np.array([
        [
            (200, height),
            (width - 200, height),
            (int(width * 0.58), int(height * 0.62)),
            (int(width * 0.42), int(height * 0.62))
        ]
    ], np.int32)

    cv2.fillPoly(mask, polygon, 255)

    cropped_edges = cv2.bitwise_and(
        edges,
        mask
    )

    lines = cv2.HoughLinesP(
        cropped_edges,
        1,
        np.pi / 180,
        threshold=30,
        minLineLength=50,
        maxLineGap=100
    )

    # =====================
    # YOLO DETECTION
    # =====================

    results = model(frame)

    sign_results = sign_model(frame, conf=0.6)

    annotated_frame = results[0].plot()

    detections = sv.Detections.from_ultralytics(
        results[0]
)

    tracked_detections = tracker.update_with_detections(
        detections
        
)
    # print("Tracked:", len(tracked_detections))  
    for detection in tracked_detections:

        x1, y1, x2, y2 = map(int, detection[0])

        scale_x = 1280 / frame.shape[1]
        scale_y = 720 / frame.shape[0]

        x1 = int(x1 * scale_x)
        y1 = int(y1 * scale_y)

        tracker_id = detection[4]

        center_y = (y1 + y2) // 2

        speed_status = "Stable"
        # print(detection)

        if tracker_id in previous_positions:

            old_y = previous_positions[tracker_id]

            if center_y > old_y + 10:
                speed_status = "Approaching"

            elif center_y < old_y - 10:
                speed_status = "Moving Away"

        previous_positions[tracker_id] = center_y

        cv2.putText(
            annotated_frame,
            f"ID:{tracker_id}",
            (x1, y1 - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,255,255),
            2
        )

        cv2.putText(
            annotated_frame,
            speed_status,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,0),
            2
        )
    

# =====================
# TRAFFIC SIGN DETECTION
# =====================

    detected_sign = "None"
    action = "Drive Normally"

    for box in sign_results[0].boxes:

        cls = int(box.cls[0])

        conf = float(box.conf[0])

        sign_name = sign_model.names[cls]
        print("Detected:", sign_name)

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        detected_sign = sign_name

        cv2.rectangle(
            annotated_frame,
            (x1, y1),
            (x2, y2),
            (255, 0, 255),
            2
        )

        cv2.putText(
            annotated_frame,
            f"{sign_name} {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 0, 255),
            2
        )

        # Driving Decisions

        sign_lower = sign_name.lower()

        if "stop" in sign_lower:
            action = "BRAKE"

        elif "no" in sign_lower and "entry" in sign_lower:
            action = "DO NOT ENTER"

        elif "red" in sign_lower:
            action = "STOP"

        elif "green" in sign_lower:
            action = "GO"

        elif "speed" in sign_lower:
            action = "FOLLOW SPEED LIMIT"

    # =====================
    # DRAW LANE LINES
    # =====================

    left_lines = []
    right_lines = []

    lane_status = "CENTER"

    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            slope = (y2 - y1) / (x2 - x1 + 0.001)

            if abs(slope) < 0.5:
                continue

            if slope < 0:
                left_lines.append(line)
            else:
                right_lines.append(line)

        if len(left_lines) > 0:

            line = left_lines[len(left_lines) // 2][0]

            x1, y1, x2, y2 = line

            cv2.line(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                5
            )

        if len(right_lines) > 0:

            line = right_lines[len(right_lines) // 2][0]

            x1, y1, x2, y2 = line

            cv2.line(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                5
            )

    # =====================
    # LANE STATUS
    # =====================

    if len(left_lines) == 0 and len(right_lines) > 0:
        lane_status = "RIGHT"

    elif len(right_lines) == 0 and len(left_lines) > 0:
        lane_status = "LEFT"

    elif len(left_lines) > 0 and len(right_lines) > 0:
        lane_status = "CENTER"
    warning = ""

    if lane_status == "LEFT":
        warning = "WARNING: DRIFTING LEFT"

    elif lane_status == "RIGHT":
        warning = "WARNING: DRIFTING RIGHT"

    else:
        warning = ""

    # =====================
    # OBJECT COUNTING
    # =====================

    car_count = 0
    person_count = 0
    emergency_warning = False

    for box in results[0].boxes:

        class_id = int(box.cls[0])
        class_name = model.names[class_id]

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        box_area = (x2 - x1) * (y2 - y1)

        if class_name == "car":
            car_count += 1

        elif class_name == "person":
            person_count += 1

        # =====================
        # VEHICLE ANALYSIS
        # =====================

        if class_name in ["car", "truck", "bus"]:

            frame_center = frame.shape[1] // 2
            vehicle_center = (x1 + x2) // 2

            distance = int(50000 / (box_area + 1))

            # Show distance above vehicle

            cv2.putText(
                annotated_frame,
                f"{distance}m",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            # Emergency brake warning

            if (
                abs(vehicle_center - frame_center) < 80
                and distance < 8
            ):

                emergency_warning = True

                cv2.putText(
                    annotated_frame,
                    "DANGER: BRAKE NOW!",
                    (20, 220),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

                cv2.putText(
                    annotated_frame,
                    f"Distance: {distance}m",
                    (20, 250),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2
                )

    # =====================
    # RISK ANALYSIS
    # =====================

    risk = "LOW"

    if car_count > 8:
        risk = "MEDIUM"

    if car_count > 15:
        risk = "HIGH"

    if person_count > 3:
        risk = "HIGH"

    # =====================
    # TRAFFIC ANALYSIS
    # =====================

    if car_count < 5:
        traffic = "LOW"

    elif car_count < 10:
        traffic = "MEDIUM"

    else:
        traffic = "HIGH"

    # =====================
    # DRIVING SCORE
    # =====================

    score = 100

    if risk == "MEDIUM":
        score -= 20

    if risk == "HIGH":
        score -= 40

    if traffic == "HIGH":
        score -= 20

    if emergency_warning:
        score -= 20

    score = max(score, 0)
    retrieved_rule = "No traffic rule available."

    if detected_sign != "None":

        query_embedding = embed_model.encode([detected_sign])

        distances, indices = index.search(
            np.array(query_embedding),
            k=1
        )

        retrieved_rule = rules[indices[0][0]]
    # ==========================
    # SEND DATA TO NODE JS
    # ==========================

    status_data = {
        "cars": car_count,
        "people": person_count,
        "traffic": traffic,
        "risk": risk,
        "lane_status": lane_status,
        "sign": detected_sign,
        "action": action,
        "score": score,
        "ai_advice": ai_advice
    }

    with open("ai_status.json", "w") as f:
        json.dump(status_data, f)

        
    if time.time() - last_llm_time > 15:

        prompt = f"""
        You are an AI driving assistant.

        Cars: {car_count}
        People: {person_count}
        Traffic: {traffic}
        Risk: {risk}
        Lane Status: {lane_status}
        Traffic Sign: {detected_sign}
        Action: {action}
        Traffic Rule:{retrieved_rule}

        Provide driving advice based on the road situation.

        Rules:
        - Give exactly 3 bullet points.
        - Maximum 5 words per bullet.
        - Focus on safety.
        - Do not explain.

        Example:
        • Maintain safe distance
        • Stay in lane
        • Watch nearby vehicles
        """

        try:

            response = ollama.chat(
                model="phi3",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            ai_advice = response["message"]["content"]
            print(ai_advice)

        except Exception as e:

            ai_advice = "LLM Error"

        last_llm_time = time.time()
        

    # =====================
    # DISPLAY INFO
    # =====================

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

    cv2.putText(
        annotated_frame,
        f"Lane Status: {lane_status}",
        (20, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 255),
        2
    )
    print(type(warning), warning)
    cv2.putText(
        annotated_frame,
        str(warning),
        (20, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )
    cv2.putText(
        annotated_frame,
        "RAG Active",
        (20, 500),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        annotated_frame,
        f"FPS: {int(fps)}",
        (20, 320),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Driving Score: {score}/100",
        (20, 360),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )
    cv2.putText(
        annotated_frame,
        f"Sign: {detected_sign}",
        (20, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 255),
        2
)

    cv2.putText(
        annotated_frame,
        f"Action: {action}",
        (20, 440),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
    annotated_frame,
    "AI Advice:",
    (750, 50),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255,255,255),
    2
)

    lines = ai_advice.split("\n")

    y = 90

    for line in lines[:3]:

        cv2.putText(
            annotated_frame,
            line[:80],
            (650, y+40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

        y += 90

    # =====================
    # EMERGENCY ALERT
    # =====================

    if person_count > 2 and car_count > 10:

        cv2.putText(
            annotated_frame,
            "EMERGENCY: CROWDED ROAD",
            (20, 650),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

    # =====================
    # SHOW VIDEO
    # =====================

    annotated_frame = cv2.resize(
        annotated_frame,
        (1280, 720)
    )

    cv2.imshow(
        "AI Driving Copilot V5",
        annotated_frame
    )

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()