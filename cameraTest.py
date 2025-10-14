import cv2

CAMERA_INDEX = 0
OUTPUT_IMAGE_PATH = 'captured_book_highres.jpg'
WARMUP_FRAMES = 5  # كافي لتثبيت التعريض والتركيز
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    raise RuntimeError("Cannot open USB camera")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# تسخين قصير
for _ in range(WARMUP_FRAMES):
    ret, frame = cap.read()

# التقاط الإطار النهائي
ret, frame = cap.read()
cap.release()
if not ret or frame is None:
    raise RuntimeError("Failed to capture frame")

# حفظ الصورة بدقة عالية وجودة JPEG 95%
cv2.imwrite(OUTPUT_IMAGE_PATH, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

# تحويلها للرمادي جاهزة لـ AKAZE
gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
print("High-resolution image captured and ready for AKAZE.")
