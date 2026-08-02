import cv2
import numpy as np

cap = cv2.VideoCapture("road.mp4")

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Resize frame
    frame = cv2.resize(frame, (1280, 720))

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blur image
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Get frame size
    height, width = edges.shape

    # Create ROI mask
    mask = np.zeros_like(edges)

    polygon = np.array([
        [
            (0, height),
            (width, height),
            (width, int(height * 0.7)),
            (0, int(height * 0.7))
        ]
    ], np.int32)

    cv2.fillPoly(mask, polygon, 255)

    # Apply mask
    cropped_edges = cv2.bitwise_and(edges, mask)

    # Detect lines
    lines = cv2.HoughLinesP(
        cropped_edges,
        1,
        np.pi / 180,
        threshold=30,
        minLineLength=50,
        maxLineGap=150
    )

    # Draw detected lines
    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )

    # -------------------------
    # Lane Position Calculation
    # -------------------------

    lane_center = width // 2

    if lines is not None:

        x_positions = []

        for line in lines:

            x1, y1, x2, y2 = line[0]

            x_positions.append(x1)
            x_positions.append(x2)

        avg_x = int(np.mean(x_positions))

        # Blue line = detected lane center
        cv2.line(
            frame,
            (avg_x, 0),
            (avg_x, height),
            (255, 0, 0),
            2
        )

        # Red line = camera center
        cv2.line(
            frame,
            (lane_center, 0),
            (lane_center, height),
            (0, 0, 255),
            2
        )

        if avg_x < lane_center - 100:
            position = "LEFT"

        elif avg_x > lane_center + 100:
            position = "RIGHT"

        else:
            position = "CENTER"

    else:
        position = "NO LANE"

    # Display lane position
    cv2.putText(
        frame,
        f"Lane: {position}",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 255),
        2
    )

    cv2.imshow("Lane Detection", frame)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()