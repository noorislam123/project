import cv2

def start_live_camera():
    # 0 هو رقم الكاميرا الافتراضية
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ فشل فتح الكاميرا")
        return

    print("📸 الكاميرا تعمل الآن.. اضغط حرف 'q' لإغلاق النافذة")

    while True:
        # التقاط إطار بإطار (Frame by Frame)
        ret, frame = cap.read()

        if not ret:
            print("❌ فشل في استقبال الصورة")
            break

        # عرض الصورة في نافذة اسمها 'Live Camera'
        cv2.imshow('Live Camera', frame)

        # التوقف إذا ضغط المستخدم على حرف 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # تنظيف الموارد
    cap.release()
    cv2.destroyAllWindows()
    print("👋 تم إغلاق الكاميرا")

if __name__ == "__main__":
    start_live_camera()