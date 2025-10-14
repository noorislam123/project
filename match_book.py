import cv2
import numpy as np
import pickle
import os
from pyzbar import pyzbar

# 🔹 مسار ملفات المزايا
FEATURES_PATH = "features"
DATASET_PATH = "dataset"

# 🔹 تحميل AKAZE detector
akaze = cv2.AKAZE_create()

# 🔹 دالة لقراءة الباركود من الصورة
def read_barcode(image):
    barcodes = pyzbar.decode(image)
    if barcodes:
        return barcodes[0].data.decode("utf-8")
    return None

# 🔹 دالة للتعرف على الكتاب باستخدام المزايا
def recognize_by_features(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    keypoints, descriptors = akaze.detectAndCompute(img, None)
    if descriptors is None:
        return None, 0

    best_match = None
    best_score = 0

    # المرور على كل ملفات المزايا المحفوظة
    for feature_file in os.listdir(FEATURES_PATH):
        with open(os.path.join(FEATURES_PATH, feature_file), "rb") as f:
            book_descriptors = pickle.load(f)

        # Brute-Force Matcher مع Hamming distance (لـ AKAZE)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(descriptors, book_descriptors)
        score = len(matches)

        if score > best_score:
            best_score = score
            best_match = feature_file.replace(".pkl", "")

    return best_match, best_score

# 🔹 الصورة الجديدة لتجربة
image_path = "test_book.jpg"  # غير الاسم حسب الصورة اللي بدك تجربها
image = cv2.imread(image_path)

# 🔹 نجرب أولًا الباركود
barcode = read_barcode(image)
if barcode:
    print(f"📦 Barcode detected: {barcode}")
    print("💡 يمكنك البحث في قاعدة البيانات باستخدام الباركود مباشرة")
else:
    print("⚠️ No barcode found, trying feature matching...")
    match_name, score = recognize_by_features(image_path)
    if match_name:
        print(f"✅ Best match: {match_name} with {score} matches")
    else:
        print("❌ No match found")
