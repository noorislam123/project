import cv2
from pyzbar import pyzbar
import numpy as np
import os
import pickle
import csv
import config

# إعداد AKAZE و FLANN
akaze = cv2.AKAZE_create()
akaze.setThreshold(config.AKAZE_THRESHOLD)

index_params = dict(algorithm=1, trees=config.FLANN_TREES)
search_params = dict(checks=config.FLANN_CHECKS)
flann = cv2.FlannBasedMatcher(index_params, search_params)

# تحميل قاعدة البيانات
def load_database():
    books_db = {}
    with open(config.DB_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            books_db[row["Barcode"]] = {
                "Folder": row["Book Folder"],
                "Title": row["Title"],
                "Author": row["Author"],
                "Shelf": row["Shelf"]
            }
    return books_db

# تحميل ميزات AKAZE
def load_features():
    features = {}
    for file in os.listdir(config.FEATURES_PATH):
        if file.endswith(".pkl"):
            book_folder = file.replace(".pkl", "")
            with open(os.path.join(config.FEATURES_PATH, file), "rb") as f:
                des = pickle.load(f)
                if des is not None:
                    des = des.astype(np.float32)
                features[book_folder] = des
    return features

books_db = load_database()
features_db = load_features()

# دالة الالتقاط والتعرف
def capture_and_identify():
    print("📸 Capturing image...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("❌ Failed to capture image")
        return False   # ← رجع False بدل لا شيء

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    zoomed = cv2.resize(enhanced, (enhanced.shape[1]*2, enhanced.shape[0]*2), interpolation=cv2.INTER_CUBIC)

    # محاولة قراءة الباركود أولاً
    barcodes = pyzbar.decode(zoomed)
    if barcodes:
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            if barcode_data in books_db:
                book = books_db[barcode_data]
                print(f"✅ Barcode matched: {book['Title']} on Shelf {book['Shelf']}")
                return True   # ← تم التعرف بنجاح
        print("⚠️ Barcode not found in DB, using AKAZE...")
    else:
        print("⚠️ No barcode found, trying AKAZE...")

    # AKAZE matching
    small_gray = cv2.resize(gray, (gray.shape[1]//2, gray.shape[0]//2))
    kp1, des1 = akaze.detectAndCompute(small_gray, None)
    if des1 is None:
        print("❌ No features detected")
        return False   # ← ما قدر يتعرف

    des1 = des1.astype(np.float32)
    best_match = None
    max_good_matches = 0

    for book_folder, des2 in features_db.items():
        if des2 is None or len(des2) == 0:
            continue
        matches = flann.knnMatch(des1, des2, k=2)
        good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]
        if len(good_matches) > max_good_matches:
            max_good_matches = len(good_matches)
            best_match = book_folder

    if best_match:
        for barcode, info in books_db.items():
            if info["Folder"] == best_match:
                print(f"🔍 Feature matched: {info['Title']} on Shelf {info['Shelf']}")
                return True   # ← تم التعرف بنجاح
    else:
        print("❌ No match found with AKAZE features")
        return False   # ← فشل بالتعرف

