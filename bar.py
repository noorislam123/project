import cv2
from pyzbar import pyzbar

# اقرأ الصورة المحفوظة
frame = cv2.imread("test_capture.jpg")

if frame is None:
    print("❌ No image found!")
else:
    print(f"✅ Image loaded: {frame.shape}")
    
    # جرب قراءة الباركود
    barcodes = pyzbar.decode(frame)
    
    print(f"📊 Barcodes found: {len(barcodes)}")
    
    if len(barcodes) == 0:
        print("❌ NO BARCODE DETECTED")
        print("\n💡 Try:")
        print("  1. Better lighting")
        print("  2. Hold barcode closer (10-15cm)")
        print("  3. Make sure barcode is not blurry")
        print("  4. Clean the barcode (no scratches)")
    else:
        for i, barcode in enumerate(barcodes):
            data = barcode.data.decode('utf-8')
            print(f"\n✅ Barcode {i+1}:")
            print(f"   Type: {barcode.type}")
            print(f"   Data: {data}")