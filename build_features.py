import cv2
import numpy as np
import os
import pickle

DATASET_PATH = "dataset"
FEATURES_PATH = "features"

akaze = cv2.AKAZE_create(
    threshold=0.001,
    nOctaves=4,
    nOctaveLayers=4
)

def preprocess(img):
    # تحسين خفيف فقط
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    return clahe.apply(img)

os.makedirs(FEATURES_PATH, exist_ok=True)

print("🚀 Extracting AKAZE features...")

for book_folder in os.listdir(DATASET_PATH):
    folder_path = os.path.join(DATASET_PATH, book_folder)
    if not os.path.isdir(folder_path):
        continue

    descriptors = []
    print(f"📘 {book_folder}")

    for img_name in os.listdir(folder_path):
        img = cv2.imread(os.path.join(folder_path, img_name), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        img = preprocess(img)
        kp, des = akaze.detectAndCompute(img, None)

        if des is not None and len(des) >= 10:
            descriptors.append(des)

    if descriptors:
        all_des = np.vstack(descriptors)

        # ✅ ضمان النوع الصحيح
        all_des = all_des.astype(np.uint8)

        with open(os.path.join(FEATURES_PATH, f"{book_folder}.pkl"), "wb") as f:
            pickle.dump(all_des, f)

        print(f"   ✅ Saved {len(all_des)} descriptors")
    else:
        print("   ⚠️ No valid features")

print("\n✨ Feature database ready!")
print(all_des.shape, all_des.dtype)
