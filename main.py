import cv2
import time

cap = cv2.VideoCapture(0)  # جرب 0 أو 1 حسب جهازك

if not cap.isOpened():
    print("Camera not found")
    exit()

print("Opening camera... wait 2 seconds")
time.sleep(2)  # استنى ثانيتين

ret, frame = cap.read()
if ret:
    cv2.imwrite("auto_snapshot.jpg", frame)
    print("Saved auto_snapshot.jpg")
    cv2.imshow("Snapshot", frame)
    cv2.waitKey(3000)  # عرض الصورة لمدة 3 ثواني
else:
    print("Failed to capture image")

cap.release()
cv2.destroyAllWindows()
