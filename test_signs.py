from ultralytics import YOLO
import cv2

model = YOLO(
    r"C:\Users\skku8\Downloads\traffic_sign\runs\detect\train-3\weights\best.pt"
)

img = cv2.imread(r"C:\Users\skku8\Downloads\traffic_sign\test\images\test_V3_1611_jpg.rf.2617791fdf0de5fb2f3d7bb9bae00004.jpg")

results = model(img, conf=0.25)

annotated = results[0].plot()

cv2.imshow("Traffic Sign Detection", annotated)
cv2.waitKey(0)
cv2.destroyAllWindows()