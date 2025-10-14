import cv2
from pyzbar import pyzbar
import os
import csv

# 📁 مسار المجلد الرئيسي للمشروع
base_path = "/home/noorislam/SmartBookReshelf/dataset"
output_csv = "/home/noorislam/SmartBookReshelf/barcode_results.csv"

# 🧾 فتح ملف CSV وكتابة العنوان
with open(output_csv, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Book Folder", "Barcode Type", "Barcode Data"])

    # المرور على جميع مجلدات الكتب
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            image_path = os.path.join(folder_path, "Barcode.jpeg")

            if os.path.exists(image_path):
                image = cv2.imread(image_path)

                if image is None:
                    print(f"{folder}: ❌ لم أستطع قراءة الصورة")
                    writer.writerow([folder, "None", "Cannot read image"])
                    continue

                # تحويل الصورة للرمادي لزيادة الدقة
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                barcodes = pyzbar.decode(gray)

                if barcodes:
                    for barcode in barcodes:
                        barcode_data = barcode.data.decode("utf-8")
                        barcode_type = barcode.type
                        print(f"{folder}: ✅ {barcode_type} -> {barcode_data}")
                        writer.writerow([folder, barcode_type, barcode_data])
                else:
                    print(f"{folder}: ⚠️ لم يتم العثور على أي باركود")
                    writer.writerow([folder, "None", "No barcode found"])
            else:
                print(f"{folder}: ❌ ملف Barcode.jpeg غير موجود")
                writer.writerow([folder, "None", "File not found"])

print(f"\n✅ تم استخراج جميع الباركودات وحفظها في الملف: {output_csv}")
