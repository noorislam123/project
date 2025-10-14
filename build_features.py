import cv2
import numpy as np
import os
import pickle

DATASET_PATH = "dataset"
FEATURES_PATH = "features"


akaze = cv2.AKAZE_create()

# 🔹 المرور على كل مجلد (كل كتاب)
for book_name in os.listdir(DATASET_PATH):
    book_path = os.path.join(DATASET_PATH, book_name)
    if not os.path.isdir(book_path):
        continue

    print(f"[+] Processing book: {book_name}")
    descriptors_list = []

    # 🔹 المرور على كل صورة داخل الكتاب
    for image_name in os.listdir(book_path):
        img_path = os.path.join(book_path, image_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            print(f"⚠️ تخطيت {image_name} (ملف غير صالح)")
            continue

        # 🔹 استخراج النقاط والمزايا
        keypoints, descriptors = akaze.detectAndCompute(img, None)

        if descriptors is not None:
            descriptors_list.append(descriptors)

    # 🔹 دمج كل المزايا للكتاب الواحد
    if descriptors_list:
        all_descriptors = np.vstack(descriptors_list)
        file_path = os.path.join(FEATURES_PATH, f"{book_name}.pkl")

        # 🔹 حفظ المزايا في ملف .pkl (pickle)
        with open(file_path, "wb") as f:
            pickle.dump(all_descriptors, f)

        print(f"✅ Saved features for {book_name} ({len(all_descriptors)} descriptors)\n")
    else:
        print(f"⚠️ No descriptors found for {book_name}\n")

print("🎉 Done! كل ملفات المزايا انحفظت في مجلد 'features/'")
