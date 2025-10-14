import cv2
from pyzbar import pyzbar
import pickle
import os
import csv
import numpy as np

# --- Load database ---
def load_database(path="book_database.csv"):
    db = {}
    if os.path.exists(path):
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                db[row["Barcode"]] = row
    return db


# --- Load features (.pkl) ---
def load_features(folder="features"):
    features = {}
    for file in os.listdir(folder):
        if file.endswith(".pkl"):
            name = file.split(".")[0]
            with open(os.path.join(folder, file), "rb") as f:
                features[name] = pickle.load(f)
    return features


# --- Match image with features ---
def match_book(test_img, features):
    akaze = cv2.AKAZE_create()
    kp2, des2 = akaze.detectAndCompute(test_img, None)

    bf = cv2.BFMatcher()
    best_match = None
    max_matches = 0

    for name, data in features.items():
        # handle either (kp, des) tuple or just descriptors
        if isinstance(data, tuple):
            des1 = data[1]
        else:
            des1 = data

        if des1 is None or des2 is None:
            continue

        matches = bf.knnMatch(des1, des2, k=2)
        good = [m for m, n in matches if m.distance < 0.75 * n.distance]

        if len(good) > max_matches:
            max_matches = len(good)
            best_match = name

    return best_match, max_matches



# --- Main process ---
def main():
    dataset_folder = "dataset"
    test_image_path = input("Enter test image path: ")

    if not os.path.exists(test_image_path):
        print("❌ Image not found.")
        return

    image = cv2.imread(test_image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Try barcode first
    barcodes = pyzbar.decode(gray)
    database = load_database()
    features = load_features()

    if barcodes:
        for barcode in barcodes:
            code = barcode.data.decode("utf-8")
            if code in database:
                info = database[code]
                print(f"\n✅ Book identified by barcode:")
                print(f"Title: {info['Title']}")
                print(f"Author: {info['Author']}")
                print(f"Shelf: {info['Shelf']}")
                return
        print("⚠️ Barcode not found in database, trying image recognition...")

    # Try image matching
    print("\n🔍 Matching by image features...")
    best_match, score = match_book(gray, features)

    if best_match:
        print(f"✅ Book identified by image: {best_match} (matches: {score})")
    else:
        print("❌ No match found.")


if __name__ == "__main__":
    main()
