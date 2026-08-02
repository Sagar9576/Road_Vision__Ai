import cv2
import numpy as np

cap = cv2.VideoCapture("road.mp4")

while True:

    ret, frame = cap.read()

    if not ret:
        print("Video Ended")
        break

    # Resize
    frame = cv2.resize(frame, (1280, 720))

    # Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge Detection
    edges = cv2.Canny(blur, 50, 150)

    # TEMPORARY: Use full mask
    height, width = edges.shape

    mask = np.zeros_like(edges)

    polygon = np.array([
        [
            (0, height),
            (width, height),
            (int(width * 0.8), int(height * 0.6)),
            (int(width * 0.2), int(height * 0.6))
        ]
    ], np.int32)

    cv2.fillPoly(mask, polygon, 255)

    cropped_edges = cv2.bitwise_and(edges, mask)

    # Detect lines
    lines = cv2.HoughLinesP(
    cropped_edges,
    1,
    np.pi / 180,
    100,
    minLineLength=200,
    maxLineGap=20
)

    line_image = frame.copy()

    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            if x2 - x1 == 0:
                continue

            slope = (y2 - y1) / (x2 - x1)

            if abs(slope) < 0.5:
                continue

            cv2.line(
                line_image,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )

    cv2.imshow("Video", frame)
    cv2.imshow("Edges", cropped_edges)
    cv2.imshow("Lane Detection", line_image)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()