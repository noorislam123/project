import cv2
from pyzbar import pyzbar
import numpy as np
import os
import pickle
import csv

# --- Load your database ---
db_file = "book_database.csv"
books_db = {}
with open(db_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        books_db[row["Barcode"]] = {
            "Folder": row["Book Folder"],
            "Title": row["Title"],
            "Author": row["Author"],
            "Shelf": row["Shelf"]
        }

# --- Load AKAZE features ---
features_path = "features/"
akaze = cv2.AKAZE_create()
akaze.setThreshold(0.005)  # يقلل عدد keypoints = أسرع

# إعداد FLANN matcher
index_params = dict(algorithm=1, trees=5)  # KDTree
search_params = dict(checks=50)
flann = cv2.FlannBasedMatcher(index_params, search_params)

def load_features():
    features = {}
    for file in os.listdir(features_path):
        if file.endswith(".pkl"):
            book_folder = file.replace(".pkl", "")
            with open(os.path.join(features_path, file), "rb") as f:
                des = pickle.load(f)
                if des is not None:
                    des = des.astype(np.float32)  # تحويل لكل ملف AKAZE
                features[book_folder] = des
    return features

features_db = load_features()

# --- Capture image from camera ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Failed to capture image")
    exit()

# --- Preprocessing for barcode detection ---
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
zoomed = cv2.resize(enhanced, (enhanced.shape[1]*2, enhanced.shape[0]*2), interpolation=cv2.INTER_CUBIC)

# --- Step 1: Barcode detection ---
barcodes = pyzbar.decode(zoomed)
if barcodes:
    found = False
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        if barcode_data in books_db:
            book = books_db[barcode_data]
            print(f"✅ Barcode matched: {book['Title']} on Shelf {book['Shelf']}")
            found = True
        else:
            print(f"⚠️ Barcode {barcode_data} not found in DB")
    if found:
        exit()
else:
    print("⚠️ No barcode found, trying AKAZE feature matching...")

# --- Step 2: AKAZE feature matching ---
# تصغير الصورة قبل استخراج descriptors لتسريع العملية
small_gray = cv2.resize(gray, (gray.shape[1]//2, gray.shape[0]//2))
kp1, des1 = akaze.detectAndCompute(small_gray, None)

if des1 is not None:
    des1 = des1.astype(np.float32)  # تحويل لـ float32 لـ FLANN

best_match = None
max_good_matches = 0

for book_folder, des2 in features_db.items():
    if des2 is None or len(des2) == 0:
        continue
    matches = flann.knnMatch(des1, des2, k=2)
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    if len(good_matches) > max_good_matches:
        max_good_matches = len(good_matches)
        best_match = book_folder

if best_match:
    # طباعة اسم الكتاب والرف بعد AKAZE
    for barcode, info in books_db.items():
        if info["Folder"] == best_match:
            print(f"🔍 Feature matched: {info['Title']} on Shelf {info['Shelf']}")
            break
else:
    print("❌ No match found with AKAZE features")
