import cv2
import numpy as np
import os
import pickle
import csv
import config
from pyzbar import pyzbar
import time

# ------------------- LCD -------------------
try:
    from RPLCD.i2c import CharLCD
    I2C_ADDRESS = getattr(config, "LCD_I2C_ADDR", 0x27)
    lcd = CharLCD(
        i2c_expander='PCF8574',
        address=I2C_ADDRESS,
        port=1,
        cols=16,
        rows=2,
        charmap='A02',
        auto_linebreaks=True
    )
    lcd.clear()
except Exception as e:
    print(f"[LCD] init failed: {e}")
    lcd = None

def lcd_status(msg):
    """اطبع رسالة على السطر الثاني بدون مسح السطر الأول"""
    if lcd is None:
        print(f"[LCD-FALLBACK] {msg}")
        return
    lcd.cursor_pos = (1,0)
    lcd.write_string(" " * 16)
    lcd.cursor_pos = (1,0)
    lcd.write_string(msg[:16])

def show_shelf_on_lcd(shelf_num=None):
    if lcd is None:
        return
    lcd.clear()
    if shelf_num is not None:
        lcd.cursor_pos = (0,0)
        lcd.write_string("Book shelfed !")
        lcd.cursor_pos = (1,0)
        lcd.write_string(f"Shelf: {shelf_num}")
    else:
        lcd.cursor_pos = (0,0)
        lcd.write_string("Book not found")

# ===================== AKAZE SETUP =====================
akaze = cv2.AKAZE_create(threshold=0.001, nOctaves=4, nOctaveLayers=4)
bf = cv2.BFMatcher(cv2.NORM_HAMMING)

# ===================== DATABASE =====================
def load_database():
    books_db = {}
    with open(config.DB_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print("CSV Columns:", reader.fieldnames)
        for row in reader:
            folder = row.get("Book_Folder") or row.get("Book Folder")
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

# ===================== FEATURES =====================
def load_features():
    features = {}
    for file in os.listdir(config.FEATURES_PATH):
        if file.endswith(".pkl"):
            with open(os.path.join(config.FEATURES_PATH, file), "rb") as f:
                des = pickle.load(f)
                if des is not None and len(des) > 0:
                    features[file.replace(".pkl", "")] = des
    return features

# ===================== BARCODE =====================
def detect_barcode(frame, books_db):
    lcd_status("Scanning Barcode")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    barcodes = pyzbar.decode(gray)
    if not barcodes:
        return False, None, None, None
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8").strip()
        print(f"📦 Barcode detected: {barcode_data}")
        if barcode_data in books_db:
            info = books_db[barcode_data]
            print(f"✅ Barcode matched: {info['Title']}")
            return True, info["Folder"], info["Shelf"], info["RFID"]
    return False, None, None, None

# ===================== AKAZE =====================
def identify_with_akaze(frame, features_db, books_db):
    lcd_status("Switching to AKAZE")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (gray.shape[1] // 2, gray.shape[0] // 2))
    kp1, des1 = akaze.detectAndCompute(gray, None)
    if des1 is None or len(des1) < 10:
        print("❌ No AKAZE features detected")
        return False, None, None, None
    best_match = None
    best_score = 0
    for folder, des2 in features_db.items():
        matches = bf.knnMatch(des1, des2, k=2)
        good = [m for m,n in matches if m.distance < 0.75 * n.distance]
        if len(good) > best_score:
            best_score = len(good)
            best_match = folder
    if best_match and best_score > 15:
        for info in books_db.values():
            if info["Folder"] == best_match:
                print(f"✅ AKAZE matched: {info['Title']}")
                return True, info["Folder"], info["Shelf"], info["RFID"]
    return False, None, None, None

# ===================== CAPTURE + IDENTIFY =====================
def capture_and_identify(books_db, features_db):
    lcd_status("Capturing Image")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False, None, None, None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return False, None, None, None

    # 1️⃣ Barcode
    found, folder, shelf, rfid = detect_barcode(frame, books_db)
    # 2️⃣ AKAZE
    if not found:
        found, folder, shelf, rfid = identify_with_akaze(frame, features_db, books_db)

    # النهاية
    if found:
        lcd_status(f"Shelf: {shelf}")
    else:
        lcd_status("Book Unknown")

    return found, folder, shelf, rfid

# ===================== MAIN TEST =====================
if __name__ == "__main__":
    books_db = load_database()
    features_db = load_features()
    f, fol, s, r = capture_and_identify(books_db, features_db)
    print(f"RESULT: found={f}, folder={fol}, shelf={s}, rfid={r}")
