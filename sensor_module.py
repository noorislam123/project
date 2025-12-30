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


def object_detected():
    signal = GPIO.input(config.IR_PIN)
    return signal == 0 if config.IR_ACTIVE_LOW else signal == 1


def build_shelf_tag_map():
    shelf_to_tag = {}
    with open(config.DB_FILE, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            shelf_to_tag[int(row["Shelf"])] = int(row["RFID_Tag"])
    return shelf_to_tag


def get_next_shelf_tag(current_shelf, shelf_to_tag):
    shelves = sorted(shelf_to_tag.keys())
    if current_shelf not in shelf_to_tag:
        return None
    i = shelves.index(current_shelf)
    if i == len(shelves) - 1:
        return getattr(config, "END_TAG", None)  # end of library
    return shelf_to_tag[shelves[i + 1]]


def start_sensor_loop():
    print("📡 System ON → Waiting for object (IR)...")

    try:
        shelf_to_tag = build_shelf_tag_map()
        print(f"🗺️ Shelf map loaded: {shelf_to_tag}")
    except Exception as e:
        print(f"❌ CSV load error: {e}")
        shelf_to_tag = {}

    try:
        while True:
            if not object_detected():
                time.sleep(0.05)
                continue

            print("\n==============================")
            print("1️⃣ IR: Object detected ✅")
            print("==============================")
            time.sleep(0.3)

            # 2) CAMERA
            print("2️⃣ CAMERA: Capturing + identifying...")
            try:
                found, book_folder, shelf, target_tag = capture_and_identify()
            except Exception as e:
                print(f"⚠️ CAMERA ERROR: {e}")
                found, book_folder, shelf, target_tag = False, None, None, None

            print(f"📌 CAMERA RESULT: found={found}, shelf={shelf}, target_tag={target_tag}")

            if not (found and shelf and target_tag):
                print("↩️ Not recognized → back to idle.")
                while object_detected():
                    time.sleep(0.05)
                continue

            target_tag = int(target_tag)
            home_tag = int(config.HOME_TAG)
            next_tag = get_next_shelf_tag(shelf, shelf_to_tag) if shelf_to_tag else getattr(config, "END_TAG", None)

            print(f"🎯 Target shelf={shelf}")
            print(f"🏷️ TARGET_TAG={target_tag}")
            print(f"🏁 NEXT/END_TAG={next_tag}")
            print(f"🏠 HOME_TAG={home_tag}")

            # 3) CONVEYOR
            print("3️⃣ RELAY+CONVEYOR: ON")
            RELAY.conveyor_on()

            # 4) MICRO SWITCH
            print("4️⃣ MICRO SWITCH: waiting press...")
            reached = micro_switch.wait_for_press(timeout=17.5)

            print("3️⃣ RELAY+CONVEYOR: OFF (safety)")
            RELAY.conveyor_off()

            if not reached:
                print("❌ Micro switch timeout → abort.")
                while object_detected():
                    time.sleep(0.05)
                continue

            print("✅ Micro switch pressed → book positioned.")

            # 5) LIFT UP SMOOTH + RFID + ULTRASONIC WINDOW
            print("5️⃣ LIFT: UP (SMOOTH continuous) 🚀")
            lift_motor.lift_up()

            scanning_started = False
            space_found = False
            shelf_full = False

            MAX_LIFT_TIME = 11
            ULTRA_INTERVAL = 0.6

            # extra lift after finding space
            EXTRA_LIFT_AFTER_SPACE = 1.0
            space_time = None

            t0 = time.time()
            last_tag_print = None

            # start timers safely
            last_ultra_check = time.time()

            # anti-false-positive: require 2 consecutive SPACE_OK
            SPACE_OK_CONFIRM = 1
            space_ok_count = 0

            # set when TARGET reached
            target_time = None
            MIN_AFTER_TARGET_DELAY = 0.4  # delay after hitting target to stabilize

            while True:
                # Safety timeout
                if time.time() - t0 > MAX_LIFT_TIME:
                    print("🛑 Safety: max lift time reached → stop")
                    break

                # Read RFID
                tag = rfid_reader.read_tag_stable()
                if tag is not None and tag != last_tag_print:
                    print(f"🏷️ RFID: {tag}")
                    last_tag_print = tag

                # Start ultrasonic window at TARGET_TAG (lift stays running)
                if (not scanning_started) and (tag == target_tag):
                    scanning_started = True
                    target_time = time.time()
                    last_ultra_check = time.time()
                    space_ok_count = 0
                    print("✅ TARGET reached → ULTRASONIC scanning ON (lift still smooth)")

                # If NEXT/END reached before finding space
                if scanning_started and (not space_found) and (next_tag is not None) and (tag == next_tag):
                    print("❌ ما في مساحة قبل NEXT/END TAG → Shelf FULL (رجّع)")
                    shelf_full = True
                    break

                # Ultrasonic checks only after scanning started
                if scanning_started and (not space_found):
                    # small delay after hitting TARGET
                    if target_time is not None and (time.time() - target_time < MIN_AFTER_TARGET_DELAY):
                        time.sleep(0.02)
                        continue

                    if time.time() - last_ultra_check >= ULTRA_INTERVAL:
                        last_ultra_check = time.time()
                        print("6️⃣ ULTRASONIC: checking space...")
                        res = space_check.check_space(samples=3, delay=0.03)

                        if res == "SPACE_OK":
                            space_ok_count += 1
                            print(f"✅ SPACE_OK confirm {space_ok_count}/{SPACE_OK_CONFIRM}")
                            if space_ok_count >= SPACE_OK_CONFIRM:
                                space_found = True
                                space_time = time.time()
                                print("🎉 SPACE_OK CONFIRMED → keep lifting 1s then stop & place")
                        else:
                            space_ok_count = 0

                # After SPACE_OK: keep lifting 1 sec then stop
                if space_found and space_time is not None:
                    if time.time() - space_time >= EXTRA_LIFT_AFTER_SPACE:
                        print("⏹️ Extra 1s done → stop lift now")
                        break

                time.sleep(0.02)

            print("5️⃣ LIFT: STOP")
            lift_motor.stop()

            # 7) DRIVE
            if space_found:
                print("7️⃣ DRIVE: placing book...")
                drive_motor.run_until_micro_on()
                print("✅ DRIVE done")
            else:
                if not scanning_started:
                    print("❌ Did not reach TARGET_TAG in time")
                elif shelf_full:
                    print("📚 Shelf FULL ")
                else:
                    print("⚠️ No space found (timeout) → treat FULL")

            # 8) RETURN HOME
            print("8️⃣ LIFT: DOWN to HOME...")
            lift_motor.lift_down()

            home_timeout = 25
            td = time.time()
            while True:
                t = rfid_reader.read_tag_stable()
                if t is not None:
                    print(f"🏷️ RFID (down): {t}")

                if t == home_tag:
                    print("✅ HOME reached → stop after 1 sec")
                    time.sleep(1)
                    lift_motor.stop()
                    break

                if time.time() - td > home_timeout:
                    print("⚠️ HOME timeout → stop for safety")
                    lift_motor.stop()
                    break

                time.sleep(0.05)

            print("🔟 Cycle END → Ready ✅")

            while object_detected():
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 Exiting system...")

    finally:
        print("🔻 Safety shutdown")
        RELAY.conveyor_off()
        lift_motor.stop()
        GPIO.cleanup()
        print("GPIO cleaned up.")


if __name__ == "__main__":
    start_sensor_loop()
