import RPi.GPIO as GPIO
import time
import csv

from cameraTest import capture_and_identify
import config
import RELAY
import microsw as micro_switch
import lift_motor
import rfid_reader
import space_check
import drive_motor

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)

micro_switch.setup()
lift_motor.setup()
drive_motor.setup()


# -------------------------------------------------
# IR DETECTION
# -------------------------------------------------
def object_detected():
    signal = GPIO.input(config.IR_PIN)
    detected = (signal == 0) if config.IR_ACTIVE_LOW else (signal == 1)
    return detected


# -------------------------------------------------
# SHELF TAG MAP (from CSV)
# -------------------------------------------------
def build_shelf_tag_map():
    shelf_to_tag = {}
    with open(config.DB_FILE, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            shelf_to_tag[int(row["Shelf"])] = int(row["RFID_Tag"])
    return shelf_to_tag


def get_next_shelf_tag(current_shelf, shelf_to_tag):
    """
    يرجع marker لنهاية نافذة الرف:
    - Shelf1 -> tag of Shelf2
    - Shelf2 -> tag of Shelf3
    - Shelf3 (آخر رف) -> END_TAG (نهاية المكتبة)
    """
    shelves = sorted(shelf_to_tag.keys())
    if current_shelf not in shelf_to_tag:
        return None

    i = shelves.index(current_shelf)

    # آخر رف -> نهاية المكتبة
    if i == len(shelves) - 1:
        return getattr(config, "END_TAG", None)

    # رف عادي -> التاغ اللي بعده
    return shelf_to_tag[shelves[i + 1]]


# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
def start_sensor_loop():
    print("📡 System started → waiting for IR object...")

    # Load shelf map once
    try:
        shelf_to_tag = build_shelf_tag_map()
        print(f"🗺️ Shelf map loaded: {shelf_to_tag}")
    except Exception as e:
        print(f"❌ Failed to load shelf map from CSV: {e}")
        shelf_to_tag = {}

    try:
        while True:

            # 1) WAIT IR
            if not object_detected():
                time.sleep(0.05)
                continue

            print("\n==============================")
            print("1️⃣ IR: Object detected ✅")
            print("==============================")
            time.sleep(0.3)  # debounce

            # 2) CAMERA
            print("2️⃣ Camera: capturing + identifying...")
            try:
                found, book_folder, shelf, target_tag = capture_and_identify()
            except Exception as e:
                print(f"⚠️ Camera error: {e}")
                found, book_folder, shelf, target_tag = False, None, None, None

            print(f"📌 Camera result: found={found}, shelf={shelf}, target_tag={target_tag}")

            if not (found and shelf and target_tag):
                print("↩️ Not recognized / missing data → back to idle.")
                while object_detected():
                    time.sleep(0.05)
                continue

            target_tag = int(target_tag)
            home_tag = int(config.HOME_TAG)
            next_tag = get_next_shelf_tag(shelf, shelf_to_tag) if shelf_to_tag else None

            print(f"✅ Target shelf={shelf}")
            print(f"🏷️ target_tag={target_tag}")
            print(f"🏁 next_marker_tag={next_tag}  (Shelf end / Library end)")
            print(f"🏠 home_tag={home_tag}")

            # 3) CONVEYOR ON
            print("3️⃣ Relay+Conveyor: ON")
            RELAY.conveyor_on()

            # 4) WAIT MICRO SWITCH
            print("4️⃣ MicroSwitch: waiting for press...")
            reached = micro_switch.wait_for_press(timeout=17.5)

            print("3️⃣ Relay+Conveyor: OFF (safety stop)")
            RELAY.conveyor_off()

            if not reached:
                print("❌ MicroSwitch not pressed → abort cycle.")
                while object_detected():
                    time.sleep(0.05)
                continue

            print("✅ MicroSwitch pressed → book at pickup position.")

            # 5) LIFT UP + RFID WINDOW SCAN
            print("5️⃣ Lift: START UP (we will NOT stop at target_tag)")
            lift_motor.lift_up()

            scanning_started = False   # يبدأ True بعد ما نقرأ target_tag
            shelf_full = False
            space_found = False

            step_up_time = 0.8         # زمن خطوة الرفع
            max_steps = 60             # حماية
            steps = 0

            last_printed_tag = None

            while steps < max_steps:

                # قراءة RFID (Stable)
                tag = rfid_reader.read_tag_stable()

                if tag is not None and tag != last_printed_tag:
                    print(f"🏷️ RFID: detected tag = {tag}")
                    last_printed_tag = tag

                # إذا بدأنا فحص المسافة ووصلنا للنهاية -> رف مليان
                if scanning_started and (next_tag is not None) and (tag == next_tag):
                    print("🛑 Reached NEXT/END tag → Shelf is FULL (no space found).")
                    shelf_full = True
                    break

                # تفعيل نافذة الفحص عند target_tag
                if (not scanning_started) and (tag == target_tag):
                    scanning_started = True
                    print("✅ Reached TARGET tag → start checking space from here until next/end tag.")

                # قبل target_tag: نرفع خطوة ونكمل
                if not scanning_started:
                    print(f"⬆️ Lifting... searching for target_tag (step {steps+1}/{max_steps})")
                    lift_motor.lift_up()
                    time.sleep(step_up_time)
                    lift_motor.stop()
                    time.sleep(0.15)
                    steps += 1
                    continue

                # 6) ULTRASONIC CHECK (داخل نافذة الرف)
                print("6️⃣ Ultrasonic: checking space...")
                result = space_check.check_space(samples=5, delay=0.05)

                if result == "SPACE_OK":
                    print("🎉 Space found ✅")
                    space_found = True
                    break

                print("❌ No space at this height → step up and re-check...")

                # خطوة رفع وارجع افحص
                lift_motor.lift_up()
                time.sleep(step_up_time)
                lift_motor.stop()
                time.sleep(0.15)
                steps += 1

            # وقف الرفع دائماً بعد الحلقة
            print("5️⃣ Lift: STOP")
            lift_motor.stop()

            # 7) DRIVE MOTOR if space_found
            if space_found:
                print("7️⃣ Drive: placing book...")
                drive_motor.run_until_micro_on()
                print("✅ Drive done → book placed.")
            else:
                if not scanning_started:
                    print("❌ Did not reach target_tag (timeout/steps) → abort.")
                elif shelf_full:
                    print("📚 Shelf FULL → no placement.")
                else:
                    print("⚠️ Max steps reached without space → treat as FULL.")

            # 8) RETURN HOME
            print("8️⃣ Lift: DOWN to HOME tag...")
            lift_motor.lift_down()

            t0 = time.time()
            home_timeout = 25

            while True:
                t = rfid_reader.read_tag_stable()
                if t is not None:
                    print(f"🏷️ RFID (descending) = {t}")

                if t == home_tag:
                    print("✅ HOME tag reached → stopping after 1 sec.")
                    time.sleep(1)
                    lift_motor.stop()
                    break

                if time.time() - t0 > home_timeout:
                    print("⚠️ HOME timeout → stop for safety.")
                    lift_motor.stop()
                    break

                time.sleep(0.05)

            print("🔟 Cycle END → Ready for next object ✅")

            # انتظر IR يرجع طبيعي
            while object_detected():
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 Exiting system...")

    finally:
        print("🔻 Safety shutdown: conveyor OFF + lift STOP + GPIO cleanup")
        RELAY.conveyor_off()
        lift_motor.stop()
        GPIO.cleanup()
        print("GPIO cleaned up.")
