import cv2
import numpy as np
import os
import pickle
import csv
import config

akaze = cv2.AKAZE_create(
    threshold=0.001,
    nOctaves=4,
    nOctaveLayers=4
)

bf = cv2.BFMatcher(cv2.NORM_HAMMING)
def load_database():
    books_db = {}

    with open(config.DB_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        print("CSV Columns:", reader.fieldnames)  # 🔍 للتأكد

        for row in reader:
            folder = (
                row.get("Book_Folder") or
                row.get("Book Folder")
            )

            if folder is None:
                print("❌ Book folder column not found in CSV")
                continue

            books_db[row["Barcode"]] = {
                "Folder": folder,
                "Title": row["Title"],
                "Shelf": int(row["Shelf"]),
                "RFID": int(row["RFID_Tag"])
            }

    return books_db

def load_features():
    features = {}
    for file in os.listdir(config.FEATURES_PATH):
        if file.endswith(".pkl"):
            with open(os.path.join(config.FEATURES_PATH, file), "rb") as f:
                des = pickle.load(f)
                if des is not None and len(des) > 0:
                    features[file.replace(".pkl", "")] = des
    return features
def identify_with_akaze(frame, features_db, books_db):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (gray.shape[1]//2, gray.shape[0]//2))

    kp1, des1 = akaze.detectAndCompute(gray, None)

    if des1 is None or len(des1) < 10:
        print("❌ No AKAZE features detected")
        return False, None, None, None

    best_match = None
    best_score = 0

    for folder, des2 in features_db.items():
        matches = bf.knnMatch(des1, des2, k=2)

        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)

        if len(good) > best_score:
            best_score = len(good)
            best_match = folder

    if best_match and best_score > 15:  # threshold مهم
        for info in books_db.values():
            if info["Folder"] == best_match:
                print(f"✅ AKAZE matched: {info['Title']}")
                return True, info["Folder"], info["Shelf"], info["RFID"]

    print("❌ No AKAZE match found")
    return False, None, None, None

if __name__ == "__main__":
    print("🚀 cameraTest started")

    books_db = load_database()
    features_db = load_features()

    print(f"📚 Books loaded: {len(books_db)}")
    print(f"🧠 Feature sets loaded: {len(features_db)}")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not opened")
        exit()

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("❌ Failed to capture frame")
        exit()

    result = identify_with_akaze(frame, features_db, books_db)
    print("RESULT:", result)
