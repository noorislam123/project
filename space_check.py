import time
import ultrasonic
import lift_motor
import rfid_reader

SPACE_THRESHOLD = 10.0   # إذا أكثر من هيك → في مساحة


def check_shelf_space(correct_shelf_tag, home_tag):
    """
    correct_shelf_tag = التاغ المفروض يكون للرف
    home_tag = التاغ اللي يعتبر OK أيضاً (عادة يكون نفسه)
    """
    ultrasonic.setup_ultrasonic()   # تجهيز التريغ + الإيكو

    print("🔎 Starting shelf space check using ultrasonic...")

    while True:
        # -------------------------------------------------
        # 1) قياس المسافة بالألتراسونيك
        # -------------------------------------------------
        distance = ultrasonic.read_distance()
        print(f"[ULTRA] Distance = {distance} cm")

        # -------------------------------------------------
        # 2) إذا في مساحة كافية → Success
        # -------------------------------------------------
        if distance is not None and distance > SPACE_THRESHOLD:
            print("✅ Space available in this shelf!")
            return True

        # -------------------------------------------------
        # 3) ما في مساحة → دفع/رفع بسيط
        # -------------------------------------------------
        print("❌ No space → moving slightly forward...")

        lift_motor.lift_up()    # حرك الموتور للأمام
        time.sleep(1)
        lift_motor.stop()
        time.sleep(3)

        # -------------------------------------------------
        # 4) فحص RFID داخل اللوب
        # -------------------------------------------------
        tag = rfid_reader.read_tag()
        print(f"[RFID ULTRA] Read tag: {tag}")

        # إذا ظهر تاغ غلط → خطأ
        if tag is not None and (tag != correct_shelf_tag and tag != home_tag):
            print("❌ ERROR: Wrong shelf tag detected during ultrasonic check!")
            return False
