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

# =========================
# LCD (I2C) SETUP
# =========================
_lcd = None

def _debug(msg: str):
    if getattr(config, "DEBUG", True):
        print(msg)

def lcd_init():
    global _lcd
    try:
        from RPLCD.i2c import CharLCD

        addr = getattr(config, "LCD_I2C_ADDR", 0x27)  # 0x27 أو 0x3F
        _lcd = CharLCD(
            i2c_expander="PCF8574",
            address=addr,
            port=1,
            cols=16,
            rows=2,
            charmap="A02",
            auto_linebreaks=False
        )
        _lcd.clear()
        lcd_show("System Ready", "Insert Book")
        _debug(f"[LCD] OK addr={hex(addr)}")
    except Exception as e:
        _lcd = None
        print(f"[LCD] init failed: {e}")

def lcd_show(line1="", line2=""):
    """يعرض سطرين على LCD (16 حرف لكل سطر)."""
    global _lcd

    l1 = str(line1)[:16].ljust(16)
    l2 = str(line2)[:16].ljust(16)

    if _lcd is None:
        _debug(f"[LCD-FALLBACK] {l1.strip()} | {l2.strip()}")
        return

    try:
        _lcd.clear()
        _lcd.cursor_pos = (0, 0)
        _lcd.write_string(l1)
        _lcd.cursor_pos = (1, 0)
        _lcd.write_string(l2)
    except Exception as e:
        _debug(f"[LCD] write failed: {e}")

# =========================
# GPIO INIT
# =========================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.IR_PIN, GPIO.IN)

micro_switch.setup()
lift_motor.setup()
drive_motor.setup()
lcd_init()


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
    lcd_show("System Ready", "Insert Book")
    _debug("📡 System ON → Waiting for object (IR)...")

    try:
        shelf_to_tag = build_shelf_tag_map()
        lcd_show("Database Loaded", "Ready")
        _debug(f"🗺️ Shelf map loaded: {shelf_to_tag}")
        time.sleep(0.8)
    except Exception as e:
        _debug(f"❌ CSV load error: {e}")
        shelf_to_tag = {}
        lcd_show("DB Error", "Check CSV")
        time.sleep(1.2)

    try:
        while True:
            # IDLE
            lcd_show("System Ready", "Insert Book")

            if not object_detected():
                time.sleep(0.05)
                continue

            # IR DETECTED
            lcd_show("Book Detected", "Processing...")
            _debug("\n==============================")
            _debug("1️⃣ IR: Object detected ✅")
            _debug("==============================")
            time.sleep(0.3)

            # CAMERA
            lcd_show("Scanning Book", "Please Wait")
            _debug("2️⃣ CAMERA: Capturing + identifying...")
            try:
                found, book_folder, shelf, target_tag = capture_and_identify()
            except Exception as e:
                _debug(f"⚠️ CAMERA ERROR: {e}")
                found, book_folder, shelf, target_tag = False, None, None, None

            _debug(f"📌 CAMERA RESULT: found={found}, shelf={shelf}, target_tag={target_tag}")

            if not (found and shelf and target_tag):
                lcd_show("Unknown Book", "Try Again")
                _debug("↩️ Not recognized → back to idle.")
                # استنى يختفي الجسم
                while object_detected():
                    time.sleep(0.05)
                continue

            target_tag = int(target_tag)
            home_tag = int(config.HOME_TAG)
            next_tag = get_next_shelf_tag(shelf, shelf_to_tag) if shelf_to_tag else getattr(config, "END_TAG", None)

            _debug(f"🎯 Target shelf={shelf}")
            _debug(f"🏷️ TARGET_TAG={target_tag}")
            _debug(f"🏁 NEXT/END_TAG={next_tag}")
            _debug(f"🏠 HOME_TAG={home_tag}")

            # CONVEYOR
            lcd_show("Moving Book", "To Position")
            _debug("3️⃣ RELAY+CONVEYOR: ON")
            RELAY.conveyor_on()

            # MICRO SWITCH
            lcd_show("Positioning", "Book...")
            _debug("4️⃣ MICRO SWITCH: waiting press...")
            reached = micro_switch.wait_for_press(timeout=17.5)

            RELAY.conveyor_off()
            _debug("3️⃣ RELAY+CONVEYOR: OFF (safety)")

            if not reached:
                lcd_show("Position Failed", "Try Again")
                _debug("❌ Micro switch timeout → abort.")
                while object_detected():
                    time.sleep(0.05)
                continue

            lcd_show("Book Positioned", "Starting Lift")
            _debug("✅ Micro switch pressed → book positioned.")
            time.sleep(0.5)

            # LIFT UP
            lcd_show("Lifting Book", "Please Wait")
            _debug("5️⃣ LIFT: UP (SMOOTH continuous) 🚀")
            lift_motor.lift_up()

            scanning_started = False
            space_found = False
            shelf_full = False

            MAX_LIFT_TIME = 11
            ULTRA_INTERVAL = 0.6

            EXTRA_LIFT_AFTER_SPACE = 1.0
            space_time = None

            t0 = time.time()
            last_tag_print = None
            last_ultra_check = time.time()

            SPACE_OK_CONFIRM = 1
            space_ok_count = 0

            target_time = None
            MIN_AFTER_TARGET_DELAY = 0.4

            while True:
                # Safety timeout
                if time.time() - t0 > MAX_LIFT_TIME:
                    _debug("🛑 Safety: max lift time reached → stop")
                    lcd_show("Lift Timeout", "Stopping...")
                    break

                # Read RFID
                tag = rfid_reader.read_tag_stable()
                if tag is not None and tag != last_tag_print:
                    _debug(f"🏷️ RFID: {tag}")
                    last_tag_print = tag

                # Start ultrasonic window at TARGET_TAG
                if (not scanning_started) and (tag == target_tag):
                    scanning_started = True
                    target_time = time.time()
                    last_ultra_check = time.time()
                    space_ok_count = 0
                    _debug("✅ TARGET reached → ULTRASONIC scanning ON (lift still smooth)")
                    lcd_show("Target Reached", "Checking Space")

                # If NEXT/END reached before finding space
                if scanning_started and (not space_found) and (next_tag is not None) and (tag == next_tag):
                    _debug("❌ ما في مساحة قبل NEXT/END TAG → Shelf FULL (رجّع)")
                    shelf_full = True
                    lcd_show("Shelf Is Full", "Returning...")
                    break

                # Ultrasonic checks only after scanning started
                if scanning_started and (not space_found):
                    if target_time is not None and (time.time() - target_time < MIN_AFTER_TARGET_DELAY):
                        time.sleep(0.02)
                        continue

                    if time.time() - last_ultra_check >= ULTRA_INTERVAL:
                        last_ultra_check = time.time()
                        _debug("6️⃣ ULTRASONIC: checking space...")
                        lcd_show("Checking Space", "Please Wait")
                        res = space_check.check_space(samples=3, delay=0.03)

                        if res == "SPACE_OK":
                            space_ok_count += 1
                            _debug(f"✅ SPACE_OK confirm {space_ok_count}/{SPACE_OK_CONFIRM}")
                            lcd_show("Space Found!", "Placing Book")
                            if space_ok_count >= SPACE_OK_CONFIRM:
                                space_found = True
                                space_time = time.time()
                        else:
                            space_ok_count = 0
                            lcd_show("No Space Yet", "Searching...")

                # After SPACE_OK: keep lifting 1 sec then stop
                if space_found and space_time is not None:
                    if time.time() - space_time >= EXTRA_LIFT_AFTER_SPACE:
                        _debug("⏹️ Extra 1s done → stop lift now")
                        lcd_show("Position Set", "Stopping Lift")
                        break

                time.sleep(0.02)

            _debug("5️⃣ LIFT: STOP")
            lift_motor.stop()
            time.sleep(2.0)

            # DRIVE
            if space_found:
                _debug("7️⃣ DRIVE: placing book...")
                lcd_show("Shelving Book", "Please Wait")
                drive_motor.run_until_micro_release(micro_switch, timeout=6.0)
                _debug("✅ DRIVE done")
                lcd_show("Book Shelved!", "Successfully")
                time.sleep(1.2)
            else:
                if not scanning_started:
                    _debug("❌ Did not reach TARGET_TAG in time")
                    lcd_show("Target Failed", "Returning...")
                elif shelf_full:
                    _debug("📚 Shelf FULL")
                    lcd_show("Shelf Is Full", "Returning...")
                else:
                    _debug("⚠️ No space found (timeout) → treat FULL")
                    lcd_show("No Space", "Returning...")

                time.sleep(1.0)

            # RETURN HOME
            _debug("8️⃣ LIFT: DOWN to HOME...")
            lcd_show("Returning", "To Home")
            lift_motor.lift_down()

            home_timeout = 25
            td = time.time()
            while True:
                t = rfid_reader.read_tag_stable()
                if t is not None:
                    _debug(f"🏷️ RFID (down): {t}")

                if t == home_tag:
                    _debug("✅ HOME reached → stop after 1 sec")
                    lcd_show("Home Reached", "Ready Soon")
                    time.sleep(1)
                    lift_motor.stop()
                    break

                if time.time() - td > home_timeout:
                    _debug("⚠️ HOME timeout → stop for safety")
                    lcd_show("Home Timeout", "Stopped")
                    lift_motor.stop()
                    break

                time.sleep(0.05)

            _debug("🔟 Cycle END → Ready ✅")
            lcd_show("System Ready", "Next Book")

            # wait until object removed
            while object_detected():
                time.sleep(0.05)

    except KeyboardInterrupt:
        _debug("🛑 Exiting system...")
        lcd_show("System Stopped", "Bye!")

    finally:
        _debug("🔻 Safety shutdown")
        lcd_show("Safety Mode", "Shutting Down")
        RELAY.conveyor_off()
        lift_motor.stop()
        GPIO.cleanup()
        try:
            if _lcd:
                _lcd.clear()
        except Exception:
            pass
        _debug("GPIO cleaned up.")


if __name__ == "__main__":
    start_sensor_loop()
